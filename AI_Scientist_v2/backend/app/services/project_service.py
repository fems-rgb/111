from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.models import Project, ProjectStatus, User, Document, AgentTask, TraceRecord, ProjectShare
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.security.sanitizer import sanitize_input
import logging

logger = logging.getLogger(__name__)



# ── 科研闭环7步标准流水线（赛道一·方向1对齐）──
AUTO_PIPELINE_STEPS = [
    {"agent_name": "knowledge_gap", "name": "知识缺口分析", "params": "", "research_question": ""},
    {"agent_name": "literature", "name": "文献综述", "params": "", "research_question": ""},
    {"agent_name": "hypothesis", "name": "假设生成", "params": "", "research_question": ""},
    {"agent_name": "hypothesis_validator", "name": "假设核验", "params": "", "research_question": ""},
    {"agent_name": "design", "name": "研究设计", "params": "", "research_question": ""},
    {"agent_name": "experiment_plan", "name": "实验规划", "params": "", "research_question": ""},
    {"agent_name": "analysis", "name": "数据分析", "params": "", "research_question": ""},
    {"agent_name": "writing", "name": "论文撰写", "params": "", "research_question": ""},
    {"agent_name": "reflection", "name": "反思迭代", "params": "", "research_question": ""},
]

async def _auto_create_pipeline(db: AsyncSession, user_id: int, project: Project):
    """项目创建时自动实例化一条7步科研闭环流水线，打通工作台↔Agent中心"""
    try:
        import uuid, copy
        from app.database.models import Pipeline
        rq = project.research_question or project.title or "请基于已有知识完成本步骤的科研任务"
        # ── 读取Agent中心保存的全局默认模板，fallback到AUTO_PIPELINE_STEPS ──
        from app.database.models import Pipeline as _P
        _default_row = (await db.execute(
            select(_P).where(_P.is_default == True).order_by(_P.created_at)
        )).scalars().first()
        steps = copy.deepcopy(_default_row.steps) if (_default_row and _default_row.steps) else copy.deepcopy(AUTO_PIPELINE_STEPS)
        for s in steps:
            s["research_question"] = rq
            s["params"] = rq
        pid = uuid.uuid4().hex[:12]
        pipe = Pipeline(
            id=pid, user_id=user_id,
            name=f"🔬 {project.title} · 科研闭环",
            description=project.description or f"由项目「{project.title}」自动生成的标准科研闭环流水线",
            steps=steps, trigger="manual", status="idle", run_count=0,
        )
        db.add(pipe)
        await db.commit()
        logger.info(f"[ProjectService] Auto pipeline created for project {project.id}: {pid}")
    except Exception as e:
        logger.warning(f"[ProjectService] Auto pipeline creation skipped: {e}")
async def create_project(db: AsyncSession, user_id: int, req: ProjectCreate) -> Project:
    project = Project(
        title=sanitize_input(req.title, 200),
        description=sanitize_input(req.description, 2000),
        research_question=sanitize_input(req.research_question, 10000),
        domain=req.domain,
        owner_id=user_id,
        tags=req.tags,
        hypothesis=sanitize_input(getattr(req, 'hypothesis', '') or '', 10000),
        verification_method=sanitize_input(getattr(req, 'verification_method', '') or '', 10000),
        visibility=getattr(req, 'visibility', 'private') or 'private',
        evidence_files=getattr(req, 'evidence_files', None) or [],
        closure_stage=0 if getattr(req, 'hypothesis', '') else -1,
        workspace=getattr(req, 'workspace', 'personal') or 'personal',
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    await _auto_create_pipeline(db, user_id, project)
    return project


async def get_user_projects(db: AsyncSession, user_id: int, status: str = None,
                            workspace: str = None, limit: int = 50, offset: int = 0) -> list:
    own_query = select(Project).where(Project.owner_id == user_id)
    if workspace and workspace != "all":
        own_query = own_query.where(Project.workspace == workspace)
    if status:
        own_query = own_query.where(Project.status == status)

    if workspace and workspace != "all":
        share_query = (
            select(Project)
            .join(ProjectShare, ProjectShare.project_id == Project.id)
            .where(ProjectShare.target_workspace == workspace)
            .where(Project.owner_id != user_id)
        )
        if status:
            share_query = share_query.where(Project.status == status)
        own_result = await db.execute(own_query.order_by(Project.updated_at.desc()))
        share_result = await db.execute(share_query.order_by(Project.updated_at.desc()))
        own_projects = list(own_result.scalars().all())
        share_projects = list(share_result.scalars().all())
        seen_ids = {p.id for p in own_projects}
        merged = own_projects + [p for p in share_projects if p.id not in seen_ids]
        return merged[offset:offset + limit]
    else:
        result = await db.execute(own_query.order_by(Project.updated_at.desc()).offset(offset).limit(limit))
        return result.scalars().all()


async def get_project(db: AsyncSession, project_id: int, user_id: int = None) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise ValueError("项目不存在")
    if user_id and project.owner_id != user_id:
        ur = await db.execute(select(User).where(User.id == user_id))
        u = ur.scalar_one_or_none()
        if not u or u.role.value != "admin":
            raise ValueError("无权访问")
    return project


async def update_project(db: AsyncSession, project_id: int, user_id: int, req: ProjectUpdate) -> Project:
    project = await get_project(db, project_id, user_id)
    for field in ["title", "description", "research_question", "domain", "tags", "hypothesis", "verification_method", "visibility", "closure_stage"]:
        val = getattr(req, field, None)
        if val is not None:
            setattr(project, field, sanitize_input(val) if isinstance(val, str) else val)
    await db.commit()
    await db.refresh(project)
    await _auto_create_pipeline(db, user_id, project)
    return project


async def delete_project(db: AsyncSession, project_id: int, user_id: int):
    project = await get_project(db, project_id, user_id)
    await db.delete(project)
    await db.commit()


async def get_project_stats(db: AsyncSession, user_id: int, workspace: str = None) -> dict:
    base_filter = [Project.owner_id == user_id]
    if workspace and workspace != "all":
        base_filter.append(Project.workspace == workspace)
    total = (await db.execute(select(func.count(Project.id)).where(*base_filter))).scalar() or 0
    running = (await db.execute(select(func.count(Project.id)).where(*base_filter, Project.status == ProjectStatus.RUNNING))).scalar() or 0
    completed = (await db.execute(select(func.count(Project.id)).where(*base_filter, Project.status == ProjectStatus.COMPLETED))).scalar() or 0
    knowledge_count = (await db.execute(select(func.count(Document.id)).where(Document.user_id == user_id))).scalar() or 0
    task_count = (await db.execute(select(func.count(AgentTask.id)).join(Project).where(*base_filter))).scalar() or 0
    trace_count = (await db.execute(select(func.count(TraceRecord.id)).join(Project).where(*base_filter))).scalar() or 0
    return {"total": total, "running": running, "completed": completed, "knowledge_count": knowledge_count, "active_pipelines": running, "hypotheses_generated": 0, "task_count": task_count, "trace_count": trace_count}


async def share_project(db: AsyncSession, project_id: int, user_id: int, target_workspace: str):
    await get_project(db, project_id, user_id)
    existing = await db.execute(select(ProjectShare).where(ProjectShare.project_id == project_id, ProjectShare.target_workspace == target_workspace))
    if existing.scalar_one_or_none():
        return {"message": "已共享到该空间"}
    share = ProjectShare(project_id=project_id, target_workspace=target_workspace, shared_by=user_id)
    db.add(share)
    await db.commit()
    return {"message": f"已共享到 {target_workspace}"}


async def unshare_project(db: AsyncSession, project_id: int, user_id: int, target_workspace: str):
    result = await db.execute(select(ProjectShare).where(ProjectShare.project_id == project_id, ProjectShare.target_workspace == target_workspace, ProjectShare.shared_by == user_id))
    share = result.scalar_one_or_none()
    if share:
        await db.delete(share)
        await db.commit()
    return {"message": "已取消共享"}


async def get_user_projects_with_progress(db: AsyncSession, user_id: int, status: str = None,
                                          workspace: str = None, limit: int = 50, offset: int = 0) -> list:
    """[stageB] 在 get_user_projects 之上批量聚合流水线进度。
    返回 dict 列表（含 progress / total_steps / completed_steps），供 ProjectListItem 直接校验。
    用 hasattr(v,'value') 兼容枚举，不依赖 TaskStatus 枚举名。
    """
    projects = await get_user_projects(db, user_id, status, workspace, limit, offset)
    if not projects:
        return []
    pids = [p.id for p in projects]
    rows = (await db.execute(
        select(AgentTask.project_id, AgentTask.status).where(AgentTask.project_id.in_(pids))
    )).all()
    stat = {}
    for pid, st in rows:
        s = stat.setdefault(pid, [0, 0])
        s[0] += 1
        sv = st.value if hasattr(st, "value") else st
        sv = str(sv).strip().lower() if sv is not None else ""
        if sv in ("completed", "complete", "done", "success", "succeeded"):
            s[1] += 1
    out = []
    for p in projects:
        d = {}
        for col in p.__table__.columns:
            v = getattr(p, col.key, None)
            if hasattr(v, "value"):
                v = v.value
            d[col.key] = v
        total, completed = stat.get(p.id, (0, 0))
        d.setdefault("hypothesis_count", 0)
        d["total_steps"] = total
        d["completed_steps"] = completed
        d["progress"] = round(completed / total * 100) if total else 0
        out.append(d)
    return out
