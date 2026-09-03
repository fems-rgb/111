"""智研星枢 - 科学问题题库 API（赛道一 · Science 125）—— 升级版"""
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.session import get_db
from app.database.models import ScienceQuestion, QuestionTask, User
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

# [fix08] 关联改为 DB 查询（QuestionTask.result.project_id），去掉全局字典

router = APIRouter(prefix="/questions", tags=["科学问题题库"])

# [fix08] 通过 DB 查询 project_id <-> question_task_id 的关联（取代全局字典）
async def _find_task_by_project(db, project_id: int) -> "QuestionTask | None":
    """根据 project_id 反查题库任务（result JSON 中存了 project_id）"""
    from sqlalchemy import select as _s
    rows = (await db.execute(
        _s(QuestionTask).where(QuestionTask.result.isnot(None))
    )).scalars().all()
    for t in rows:
        if (t.result or {}).get("project_id") == project_id:
            return t
    return None


async def _find_task_by_id(db, task_id: int) -> "QuestionTask | None":
    from sqlalchemy import select as _s
    return (await db.execute(
        _s(QuestionTask).where(QuestionTask.id == task_id)
    )).scalar_one_or_none()



# ─── 请求/响应模型 ──────────────────────────────────────────────

class GenerateRequest(BaseModel):
    question_id: int
    custom_prompt: str = ""
    pipeline_id: Optional[str] = None  # 可选：通过流水线生成

class BatchGenerateRequest(BaseModel):
    question_ids: list[int] = Field(..., min_length=1, max_length=50)
    custom_prompt: str = ""
    pipeline_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    task_id: int
    feedback: str

class CreateQuestionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    title_en: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    keywords: Optional[list[str]] = []
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    source: str = "user_custom"


# ─── 获取题目列表 ──────────────────────────────────────────────

@router.get("/")
async def list_questions(
    category: str | None = None,
    keyword: str | None = None,
    difficulty: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页获取科学问题列表，支持分类、关键词、难度筛选"""
    query = select(ScienceQuestion).where(ScienceQuestion.is_active == True)

    if category:
        query = query.where(ScienceQuestion.category == category)
    if difficulty:
        query = query.where(ScienceQuestion.difficulty == difficulty)
    if keyword:
        kw_filter = (
            ScienceQuestion.title.ilike(f"%{keyword}%")

            | ScienceQuestion.description.ilike(f"%{keyword}%")
            | ScienceQuestion.title_en.ilike(f"%{keyword}%")
        )
        query = query.where(kw_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = query.order_by(ScienceQuestion.sort_order, ScienceQuestion.id)
    items_q = items_q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(items_q)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "question_id": r.question_id,
                "title": r.title,
                "title_en": r.title_en,
                "category": r.category,
                "description": r.description,
                "keywords": r.keywords or [],
                "difficulty": r.difficulty,
                "source": r.source,
            }
            for r in rows
        ],
    }


# ─── 获取单个题目详情 ──────────────────────────────────────────

@router.get("/my-tasks")
async def my_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的题目生成任务历史"""
    base = select(QuestionTask).where(QuestionTask.user_id == current_user.id)

    if status and status.strip():
        base = base.where(QuestionTask.status == status)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = base.order_by(QuestionTask.created_at.desc())
    items_q = items_q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(items_q)).scalars().all()

    # 批量获取题目标题
    qids = list(set(r.question_id for r in rows))
    title_map = {}
    if qids:
        qq = select(ScienceQuestion.question_id, ScienceQuestion.title).where(
            ScienceQuestion.question_id.in_(qids)
        )
        qrows = (await db.execute(qq)).all()
        title_map = {r.question_id: r.title for r in qrows}

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "task_id": r.id,
                "question_id": r.question_id,
                "question_title": title_map.get(r.question_id, f"题目#{r.question_id}"),
                "status": r.status,
                "version": r.version,
                "progress": r.progress if r.progress is not None and r.progress > 0 else ((r.result or {}).get("progress", 0) if r.status != "completed" else 100),
                "document_path": r.document_path,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in rows
        ],
    }
@router.get("/{question_id}")
async def get_question_detail(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个题目的完整详情"""
    q = select(ScienceQuestion).where(
        ScienceQuestion.question_id == question_id,
        ScienceQuestion.is_active == True,
    )
    row = (await db.execute(q)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 同时查该用户对此题目的任务历史
    tasks_q = (
        select(QuestionTask)
        .where(
            QuestionTask.question_id == question_id,
            QuestionTask.user_id == current_user.id,
        )
        .order_by(QuestionTask.created_at.desc())
        .limit(10)
    )
    task_rows = (await db.execute(tasks_q)).scalars().all()

    return {
        "question_id": row.question_id,
        "title": row.title,
        "title_en": row.title_en,
        "category": row.category,
        "description": row.description,
        "keywords": row.keywords or [],
        "difficulty": row.difficulty,
        "source": row.source,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "task_history": [
            {
                "task_id": t.id,
                "status": t.status,
                "version": t.version,
                "document_path": t.document_path,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in task_rows
        ],
    }


# ─── 获取分类统计 ──────────────────────────────────────────────

@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有分类及题目数量"""
    q = (
        select(ScienceQuestion.category, func.count().label("count"))
        .where(ScienceQuestion.is_active == True)
        .group_by(ScienceQuestion.category)
        .order_by(func.count().desc())
    )
    rows = (await db.execute(q)).all()
    return [{"category": r.category, "count": r.count} for r in rows]


# ─── 用户自主添加题目 ──────────────────────────────────────────

@router.post("/create")
async def create_question(
    req: CreateQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户自主添加自定义科学问题"""
    # 获取当前最大 question_id
    max_q = select(func.max(ScienceQuestion.question_id))
    max_id = (await db.execute(max_q)).scalar() or 0

    new_q = ScienceQuestion(
        question_id=max_id + 1,
        title=req.title,
        title_en=req.title_en,
        category=req.category,
        description=req.description or "",
        keywords=req.keywords or [],
        difficulty=req.difficulty,
        source=req.source,
        is_active=True,
        sort_order=max_id + 1,
    )
    db.add(new_q)
    await db.commit()
    await db.refresh(new_q)

    logger.info(f"用户 {current_user.id} 添加自定义题目: question_id={new_q.question_id}, title={req.title}")

    return {
        "message": "题目添加成功",
        "question_id": new_q.question_id,
        "title": new_q.title,
    }


# ─── 生成题目文档（异步任务） ──────────────────────────────────





# ─── 流水线完成回调（签名匹配 event_bus.emit 的 kwargs 解包）──────────
async def on_project_completed(project_id=None, user_id=None, **_kw):
    """AI流水线真正完成后，回写结果到对应的题库任务"""
    from app.database.session import AsyncSessionLocal
    from app.database.models import Project, QuestionTask, ExperimentRun
    from sqlalchemy import select
    import os as _os

    if not project_id:
        return

    async with AsyncSessionLocal() as db:
        task = await _find_task_by_project(db, int(project_id))
        task_id = task.id if task else None
        if not task_id:
            return
        try:
            project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
            if not project:
                return
            task = (await db.execute(select(QuestionTask).where(QuestionTask.id == task_id))).scalar_one_or_none()
            if not task:
                return

            report_path = _os.path.join(_os.getcwd(), "output", str(project_id), "report.md")
            if _os.path.exists(report_path):
                task.document_path = report_path
            elif project.final_output:
                doc_dir = _os.path.join(_os.getcwd(), "output", "questions", str(task_id))
                _os.makedirs(doc_dir, exist_ok=True)
                doc_path = _os.path.join(doc_dir, "report.md")
                with open(doc_path, "w", encoding="utf-8") as f:
                    f.write(project.final_output)
                task.document_path = doc_path

            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            result = task.result or {}
            result["content"] = project.final_output or ""

            # [fix-final-A] 从 project.evidence_files 归集图表/视频 -> result
            try:
                _ev = list(getattr(project, "evidence_files", None) or [])
                _figs = [str(x) for x in _ev if isinstance(x, str) and str(x).lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".gif"))]
                _vids = [str(x) for x in _ev if isinstance(x, str) and str(x).lower().endswith((".mp4", ".gif", ".avi", ".mov", ".webm"))]
                # 兜底：从 ExperimentRun 再收集一次，避免丢失
                try:
                    _runs = (await db.execute(
                        select(ExperimentRun).where(ExperimentRun.project_id == project_id)
                    )).scalars().all()
                    for _r in _runs:
                        for _c in (_r.charts or []):
                            _p = _c.get("path") if isinstance(_c, dict) else str(_c)
                            if _p and _p not in _figs:
                                _figs.append(_p)
                        if _r.video_path and _r.video_path not in _vids:
                            _vids.append(_r.video_path)
                except Exception as _er:
                    print(f"[on_completed] ExperimentRun 兜底收集失败: {_er}")
                result["figures"] = _figs
                result["videos"] = _vids
                print(f"[on_completed] project {project_id} figures={len(_figs)} videos={len(_vids)}")
            except Exception as _e:
                print(f"[on_completed] gather artifacts error: {_e}")

            result["project_id"] = project_id
            task.result = result
            await db.commit()
            logger.info(f"✅ 题库任务回写完成: task_id={task_id}, project_id={project_id}, doc={task.document_path}")
        except Exception as e:
            logger.error(f"❌ 题库任务回写失败: task_id={task_id}, error={e}", exc_info=True)
            try:
                task = (await db.execute(select(QuestionTask).where(QuestionTask.id == task_id))).scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_message = f"结果回写失败: {str(e)[:200]}"
                    task.completed_at = datetime.now(timezone.utc)
                    await db.commit()
            except Exception:
                pass
async def on_agent_step_completed(project_id=None, task_id=None, **_kw):
    """每完成一个Agent步骤，按 已完成步数/总步数 实时更新题库任务进度"""
    from app.database.session import AsyncSessionLocal
    from app.database.models import QuestionTask, AgentTask
    from sqlalchemy import select, func

    if not project_id:
        return
    qt_ = await _find_task_by_project(db, int(project_id))
    question_task_id = qt_.id if qt_ else None
    if not question_task_id:
        return

    async with AsyncSessionLocal() as db:
        try:
            tasks_r = (await db.execute(
                select(AgentTask).where(AgentTask.project_id == project_id).order_by(AgentTask.step_order)
            )).scalars().all()
            total = len(tasks_r) or 1
            done = sum(1 for t in tasks_r if t.status == "completed")
            progress = min(int(30 + (done / total) * 65), 95)

            task = (await db.execute(select(QuestionTask).where(QuestionTask.id == question_task_id))).scalar_one_or_none()
            if task and task.status == "running":
                task.progress = progress
                await db.commit()
        except Exception as e:
            logger.debug(f"进度同步失败: {e}")


from app.core.events import event_bus, Events
from app.utils.cleanup import clean_task_files, clean_project_files
async def on_project_failed(project_id=None, error=None, **_kw):
    """流水线失败时，同步把对应的题库任务标记为 failed"""
    from app.database.session import AsyncSessionLocal
    from app.database.models import QuestionTask
    from sqlalchemy import select
    if not project_id:
        return
    task = await _find_task_by_project(db, int(project_id))
    task_id = task.id if task else None
    if not task_id:
        return
    async with AsyncSessionLocal() as db:
        try:
            task = (await db.execute(select(QuestionTask).where(QuestionTask.id == task_id))).scalar_one_or_none()
            if task and task.status == "running":
                task.status = "failed"
                task.error_message = f"流水线执行失败: {str(error)[:300]}" if error else "流水线执行失败"
                task.completed_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info(f"❌ 题库任务同步失败状态: task_id={task_id}, project_id={project_id}")
        except Exception as e:
            logger.error(f"同步题库失败状态出错: {e}", exc_info=True)

event_bus.on(Events.PROJECT_COMPLETED, on_project_completed)
event_bus.on(Events.AGENT_COMPLETED, on_agent_step_completed)
event_bus.on(Events.PROJECT_FAILED, on_project_failed)



@router.post("/generate")
async def generate_question_doc(
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交题目文档生成任务（支持直接生成或通过流水线）"""
    q = select(ScienceQuestion).where(ScienceQuestion.question_id == req.question_id)
    question = (await db.execute(q)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    result_meta = {}
    if req.custom_prompt:
        result_meta["custom_prompt"] = req.custom_prompt
    if req.pipeline_id:
        result_meta["pipeline_id"] = req.pipeline_id
        result_meta["generation_mode"] = "pipeline"
    else:
        result_meta["generation_mode"] = "direct"

    task = QuestionTask(
        question_id=req.question_id,
        user_id=current_user.id,
        status="running",
        result=result_meta,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    logger.info(
        f"题目生成任务已创建: task_id={task.id}, question_id={req.question_id}, "
        f"mode={'pipeline:'+req.pipeline_id if req.pipeline_id else 'direct'}"
    )

    # 启动后台执行
    background_tasks.add_task(
        _execute_question_generation,
        task_id=task.id,
        question_id=req.question_id,
        question_title=question.title,
        question_desc=question.description or "",
        custom_prompt=req.custom_prompt,
        pipeline_id=req.pipeline_id,
        user_id=current_user.id,
    )

    return {"task_id": task.id, "status": "running", "message": "任务已提交，正在生成中"}


async def _execute_question_generation(
    task_id: int,
    question_id: int,
    question_title: str,
    question_desc: str,
    custom_prompt: str,
    pipeline_id: str | None,
    user_id: int,
):
    """后台执行题目文档生成"""
    from app.database.session import AsyncSessionLocal
    from datetime import datetime, timezone

    try:
        async with AsyncSessionLocal() as db:
            task_q = select(QuestionTask).where(QuestionTask.id == task_id)
            task = (await db.execute(task_q)).scalar_one_or_none()
            if not task:
                return

            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            await db.commit()

            # 构建研究问题文本
            research_text = f"科学问题：{question_title}"
            if question_desc:
                research_text += f"\n\n问题描述：{question_desc}"
            if custom_prompt:
                research_text += f"\n\n用户补充要求：{custom_prompt}"

            # ── 内置流水线映射 ──
            BUILTIN_PIPELINE_STEPS = {

        'builtin_default_mode': ['knowledge_gap', 'literature', 'hypothesis', 'design', 'experiment_plan', 'analysis', 'writing', 'review', 'reflection'],                'builtin_full_closure': ['knowledge_gap', 'literature', 'hypothesis', 'design', 'experiment_plan', 'analysis', 'writing', 'review', 'reflection'],
                'builtin_quick_analysis': ['knowledge_gap', 'literature', 'hypothesis'],
                'builtin_literature_hypothesis': ['knowledge_gap', 'literature', 'hypothesis', 'design'],
            }

            if pipeline_id == 'agent_center_current':
                # Agent中心当前编排: 先创建Project, 再走 orchestrator 默认全自主流水线
                from app.database.models import Project, ProjectStatus
                project = Project(
                    title=f"[题库] {question_title[:80]}",
                    research_question=research_text,
                    domain="人文社科",
                    status=ProjectStatus.DRAFT,
                    owner_id=user_id,
                )
                db.add(project)
                await db.commit()
                await db.refresh(project)

                _r = task.result or {}
                _r["project_id"] = project.id
                _r["generation_mode"] = "agent_center"
                _r["pipeline_id"] = pipeline_id
                task.result = _r
                task.progress = 30
                task.status = "running"
                await db.commit()

                from app.agents.orchestrator import orchestrator
                await orchestrator.start_project(db, project.id, user_id, custom_pipeline=None)
                # 确认任务状态为 running
                if task.status not in ("completed", "failed"):
                    task.status = "running"
                    await db.commit()
                logger.info(f"Agent中心编排已启动: task_id={task_id}, project_id={project.id}")
                return
            if pipeline_id in BUILTIN_PIPELINE_STEPS:
                from app.database.models import Project, ProjectStatus
                project = Project(
                    title=f"[题库] {question_title[:80]}",
                    research_question=research_text,
                    domain="人文社科",
                    status=ProjectStatus.DRAFT,
                    owner_id=user_id,
                )
                db.add(project)
                await db.commit()
                await db.refresh(project)

                result = task.result or {}
                result["project_id"] = project.id
                result["generation_mode"] = "builtin_pipeline"
                result["pipeline_id"] = pipeline_id
                task.result = result
                task.progress = 30
                await db.commit()

                from app.agents.orchestrator import orchestrator
                custom_steps = BUILTIN_PIPELINE_STEPS[pipeline_id]
                # 记录项目和任务的关联，用于流水线完成后回写结果
                # 把 project_id 写进 result，前端用于跳转工作台
                _r = task.result or {}
                _r["project_id"] = project.id
                _r["generation_mode"] = "builtin_pipeline"
                _r["pipeline_id"] = pipeline_id
                task.result = _r
                task.progress = 30
                task.status = "running"
                await db.commit()
                # 启动异步流水线，不阻塞当前请求
                await orchestrator.start_project(db, project.id, user_id, custom_pipeline=custom_steps)
                # 确认任务状态为 running
                if task.status not in ("completed", "failed"):
                    task.status = "running"
                    await db.commit()
                logger.info(f"内置流水线已启动: task_id={task_id}, pipeline={pipeline_id}, project_id={project.id}")
                return

            if pipeline_id:
                # 通过流水线执行：创建临时项目并触发流水线
                from app.database.models import Project, ProjectStatus
                project = Project(
                    title=f"[题库] {question_title[:80]}",
                    research_question=research_text,
                    domain="人文社科",
                    status=ProjectStatus.DRAFT,
                    owner_id=user_id,
                )
                db.add(project)
                await db.commit()
                await db.refresh(project)

                # 更新任务结果中的项目ID
                result = task.result or {}
                result["project_id"] = project.id
                result["generation_mode"] = "pipeline"
                task.result = result

                # 更新进度
                task.progress = 30
                await db.commit()


                # 注册 project -> question_task 映射，供回调回写状态

                # 标记为 running，让前端轮询持续
                task.status = "running"
                task.progress = 30
                await db.commit()

                # 触发流水线执行（fire-and-forget，回调负责 completed/failed）
                from app.agents.orchestrator import orchestrator
                await orchestrator.start_project(db, project.id, user_id)
                logger.info(f"流水线已启动: task_id={task_id}, project_id={project.id}")
            else:
                # 直接生成：调用 AI 生成研究文档
                from app.agents.qwen_client import call_qwen

                # 更新进度: 开始生成
                result = task.result or {}
                task.progress = 10
                task.result = result
                await db.commit()

                system_prompt = """你是一位资深的人文社科学术研究助手与科研方法论专家。请根据给定的科学问题，撰写一份完整的、可对标顶级期刊水平的研究分析报告。

报告必须严格包含以下9个部分，每部分需有实质性内容，禁止空泛表述：

## 1. 问题理解与知识缺口分析
- 明确研究对象（Research Object）
- 提取关键变量（自变量、因变量、中介/调节变量、控制变量）
- 梳理已有共识与争议焦点
- 界定3-5个具体的知识缺口（Knowledge Gaps）
- 标注约束条件（方法局限、数据可得性、伦理限制）

## 2. 知识整合与文献证据
- 核心概念界定（中英文对照，含操作性定义）
- 理论基础（至少3个理论框架，含代表学者、核心观点、适用边界）
- 研究脉络（按时间线梳理关键里程碑，≥5个节点）
- 研究空白分析（指出现有文献的具体不足）
- 本研究的学术定位（填补哪个空白、与哪些研究对话）

## 3. 候选假设生成
提出2-4个相互竞争、可证伪的科学假设，每个假设包含：
- 假设陈述（具体命题，非泛泛建议）
- 依据（引用具体文献/事实/数据作为证据链）
- 变量关系（自变量→因变量的作用机制）
- 验证方法（实验/调查/计量模型等可操作方案）
- 可验证性评分（1-10分，10=完全可实证检验）

## 4. 研究设计
- 研究假设汇总表
- 理论框架与概念模型图（文字描述）
- 数据来源与样本筛选标准
- 变量操作化定义表（含测量方式、量表来源）
- 计量模型设定（数学表达式）
- 识别策略与内生性处理方案
- 稳健性检验方案（≥3种）

## 5. 实验任务规划
针对每个假设给出独立验证方案：
- 研究设计类型（实验/准实验/调查/案例）
- 样本量计算依据与抽样方法
- 数据采集工具、流程、时间节点
- 分析方法（模型公式、软件、关键参数）
- 判定标准（支持/拒绝假设的统计阈值）
- 风险控制（混淆变量、缺失数据、伦理审查）

## 6. 数据分析方案
提供完整可运行的Python代码框架：
- 数据准备（清洗规则、变量构建、描述性统计）
- 主回归分析代码（pandas/statsmodels）
- 稳健性检验代码（≥3种）
- 可视化方案代码
- 结果解读模板

## 7. 研究方案输出
整合为规范学术论文格式：
- 标题（20字以内）
- 摘要（300字，含目的、方法、核心发现、理论贡献）
- 关键词（3-5个，中英文对照）
- 引言（问题提出→文献缺口→本研究切入点→边际贡献）
- 文献综述与研究假设
- 研究设计
- 预期实证分析框架
- 结论与讨论框架

## 8. 核验与评审
以严格审稿人视角自评：
- 各维度评分表（创新性25%/严谨性30%/贡献度25%/规范性20%，1-10分）
- 审稿结论（接受/小修/大修/拒绝）
- 优点（≥3条）
- 不足（≥3条）
- 修改建议（≥5条，具体可操作）

## 9. 反思与迭代记录
- 假设评估表（每个假设的支持度、证据强度、状态）
- 关键发现与异常模式
- 迭代修正建议（细化/拆分/合并/替换，含优先级）
- 闭环成熟度评分（0-100%）
- 下一轮研究重点

【质量红线】
- 总字数控制在6000-9000字
- 每部分必须有实质性内容，禁止"待补充"占位
- 所有引用使用GB/T 7714-2015格式
- 实证结果需报告具体数值（系数、标准误、p值、R²等）
- 使用Markdown格式，章节标题用##，子标题用###
- 语言学术规范、逻辑清晰、论证严密"""

                user_msg = research_text

                # 更新进度: 调用AI中
                task.progress = 30
                task.result = result
                await db.commit()

                response = await call_qwen(system_prompt, user_msg)

                # 更新进度: AI返回，处理中
                task.progress = 70
                task.result = result
                await db.commit()

                content = response.get("content", "") if isinstance(response, dict) else str(response)

                # 保存结果
                result["content"] = content
                task.progress = 100
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)

                # 写入文档文件并记录路径
                import os as _os
                _doc_dir = _os.path.join(_os.getcwd(), "output", "questions", str(task_id))
                _os.makedirs(_doc_dir, exist_ok=True)
                _doc_path = _os.path.join(_doc_dir, "report.md")
                with open(_doc_path, "w", encoding="utf-8") as f:
                    f.write(content)
                task.document_path = _doc_path

                await db.commit()
                logger.info(f"直接生成完成: task_id={task_id}, content_len={len(content)}, doc={_doc_path}")

    except Exception as e:
        logger.error(f"题目生成失败: task_id={task_id}, error={e}", exc_info=True)
        try:
            async with AsyncSessionLocal() as db:
                task_q = select(QuestionTask).where(QuestionTask.id == task_id)
                task = (await db.execute(task_q)).scalar_one_or_none()
                if task:
                    task.status = "failed"
                    task.error_message = str(e)[:500]
                    task.completed_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception as e2:
            logger.error(f"更新失败状态也出错: {e2}")


# ─── 批量生成题目文档 ──────────────────────────────────────────

@router.post("/batch-generate")
async def batch_generate_docs(
    req: BatchGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量提交多个题目的文档生成任务"""
    tasks_created = []
    errors = []

    for qid in req.question_ids:
        q = select(ScienceQuestion).where(ScienceQuestion.question_id == qid)
        question = (await db.execute(q)).scalar_one_or_none()
        if not question:
            errors.append({"question_id": qid, "error": "题目不存在"})
            continue

        result_meta = {"generation_mode": "batch"}
        if req.custom_prompt:
            result_meta["custom_prompt"] = req.custom_prompt
        if req.pipeline_id:
            result_meta["pipeline_id"] = req.pipeline_id
            result_meta["generation_mode"] = "batch_pipeline"

        task = QuestionTask(
            question_id=qid,
            user_id=current_user.id,
            status="running",
            result=result_meta,
        )
        db.add(task)
        await db.flush()
        tasks_created.append({"question_id": qid, "task_id": task.id, "title": question.title, "desc": question.description or ""})

    await db.commit()

    # 为每个任务启动后台执行
    for tc in tasks_created:
        background_tasks.add_task(
            _execute_question_generation,
            task_id=tc["task_id"],
            question_id=tc["question_id"],
            question_title=tc["title"],
            question_desc=tc["desc"],
            custom_prompt=req.custom_prompt,
            pipeline_id=req.pipeline_id,
            user_id=current_user.id,
        )

    logger.info(
        f"批量生成任务已创建: user={current_user.id}, "
        f"success={len(tasks_created)}, failed={len(errors)}"
    )

    return {
        "message": f"已提交 {len(tasks_created)} 个任务，正在生成中",
        "tasks": [{"question_id": t["question_id"], "task_id": t["task_id"]} for t in tasks_created],
        "errors": errors,
        "total_submitted": len(tasks_created),
    }


# ─── 查询任务状态 ──────────────────────────────────────────────

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询生成任务状态与结果"""
    q = select(QuestionTask).where(
        QuestionTask.id == task_id,
        QuestionTask.user_id == current_user.id,
    )
    task = (await db.execute(q)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 同时返回题目标题
    qq = select(ScienceQuestion).where(ScienceQuestion.question_id == task.question_id)
    question = (await db.execute(qq)).scalar_one_or_none()

    return {
        "task_id": task.id,
        "question_id": task.question_id,
        "question_title": question.title if question else None,
        "status": task.status,
        "progress": task.progress if task.progress is not None and task.progress > 0 else ((task.result or {}).get("progress", 0) if task.status != "completed" else 100),
        "result": task.result,
        "document_path": task.document_path,
        "version": task.version,
        "feedback": task.feedback,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


# ─── 读取文档内容 ──────────────────────────────────────────────

@router.get("/tasks/{task_id}/document")
async def get_task_document(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """读取任务生成的文档内容"""
    q = select(QuestionTask).where(
        QuestionTask.id == task_id,
        QuestionTask.user_id == current_user.id,
    )
    task = (await db.execute(q)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 尝试从文件读取，兼容伪路径/缺失文件
    doc_path = task.document_path
    content_from_file = None
    if doc_path:
        import os as _os
        abs_path = doc_path if _os.path.isabs(doc_path) else _os.path.join(_os.getcwd(), doc_path)
        if _os.path.exists(abs_path):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content_from_file = f.read()
            except Exception:
                pass

    if content_from_file:
        return {"task_id": task_id, "content": content_from_file, "source": "file", "path": doc_path}

    # fallback to result JSON
    content = ""
    if task.result and isinstance(task.result, dict):
        content = task.result.get("content", "") or task.result.get("document", "") or ""
    if not content:
        raise HTTPException(status_code=404, detail="文档尚未生成或文件丢失")
    return {"task_id": task_id, "content": content, "source": "result"}


# ─── 提交反馈 / 迭代 ──────────────────────────────────────────



# ─── 重试失败任务 ──────────────────────────────────────────────

class RetryRequest(BaseModel):
    custom_prompt: str = ""  # 可选：重试时追加新的提示词

@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_id: int,
    req: RetryRequest = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重试一个失败的任务：基于原任务的题目和配置，创建新任务并重新执行"""
    if req is None:
        req = RetryRequest()

    # 查找原任务
    q = select(QuestionTask).where(
        QuestionTask.id == task_id,
        QuestionTask.user_id == current_user.id,
    )
    old_task = (await db.execute(q)).scalar_one_or_none()
    if not old_task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if old_task.status not in ("failed", "completed"):
        raise HTTPException(status_code=400, detail=f"只有失败或已完成的任务可以重试，当前状态: {old_task.status}")

    # 获取原题目标题
    qq = select(ScienceQuestion).where(ScienceQuestion.question_id == old_task.question_id)
    question = (await db.execute(qq)).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="关联题目不存在")

    # 从原任务提取配置
    old_result = old_task.result or {}
    pipeline_id = old_result.get("pipeline_id")
    old_prompt = old_result.get("custom_prompt", "")
    merged_prompt = old_prompt
    if req.custom_prompt:
        merged_prompt = f"{old_prompt}\n\n【重试补充】{req.custom_prompt}" if old_prompt else req.custom_prompt

    # 创建新任务（version +1）
    new_version = old_task.version + 1
    result_meta = dict(old_result)
    result_meta["retried_from"] = task_id
    result_meta["retry_version"] = new_version
    if merged_prompt:
        result_meta["custom_prompt"] = merged_prompt

    new_task = QuestionTask(
        question_id=old_task.question_id,
        user_id=current_user.id,
        status="running",
        version=new_version,
        result=result_meta,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    logger.info(
        f"任务重试已创建: new_task_id={new_task.id}, old_task_id={task_id}, "
        f"question_id={old_task.question_id}, version={new_version}"
    )

    background_tasks.add_task(
        _execute_question_generation,
        task_id=new_task.id,
        question_id=old_task.question_id,
        question_title=question.title,
        question_desc=question.description or "",
        custom_prompt=merged_prompt,
        pipeline_id=pipeline_id,
        user_id=current_user.id,
    )

    return {
        "task_id": new_task.id,
        "status": "running",
        "message": f"重试任务已提交 (v{new_version})",
        "retried_from": task_id,
        "version": new_version,
    }

# ─── 删除任务 ──────────────────────────────────────────

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除单个任务，并级联删除其关联的 Project + ExperimentRun"""
    q = select(QuestionTask).where(
        QuestionTask.id == task_id,
        QuestionTask.user_id == current_user.id,
    )
    task = (await db.execute(q)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 收集关联的 project_id（多来源，避免依赖单一字段）
    # [bidirectional] 级联删除关联的 Project（关联键 = question_id）
    # 链路: QuestionTask -> ScienceQuestion(question_id) -> Project(title)
    from app.database.models import Project as _Proj, ScienceQuestion as _SQ, ExperimentRun as _ExpRun
    project_ids = set()
    try:
        # 兜底：ExperimentRun（如果有的话）
        _runs = (await db.execute(
            select(_ExpRun).where(_ExpRun.question_task_id == task.id)
        )).scalars().all()
        for _r in _runs:
            if _r.project_id:
                project_ids.add(int(_r.project_id))
            await db.delete(_r)
        # 主路径：ScienceQuestion.question_id -> Project.title 前缀
        _sq_obj = (await db.execute(
            select(_SQ).where(_SQ.question_id == task.question_id)
        )).scalar_one_or_none()
        if _sq_obj:
            _kw = (_sq_obj.title or "").replace("[题库] ", "", 1).strip().rstrip("？?").rstrip("?")
            _projs = (await db.execute(
                select(_Proj).where(
                    _Proj.title.like(f"[题库] {_kw}%"),
                    _Proj.owner_id == current_user.id,
                )
            )).scalars().all()
            for _p in _projs:
                project_ids.add(int(_p.id))
            # 兜底：精确匹配
            if not _projs and _sq_obj.title:
                _p2 = (await db.execute(
                    select(_Proj).where(_Proj.title == f"[题库] {_sq_obj.title}")
                )).scalar_one_or_none()
                if _p2:
                    project_ids.add(int(_p2.id))
        print(f"[cascade-B] task {task_id} -> project_ids={project_ids}")
        for _pid in project_ids:
            _p = (await db.execute(select(_Proj).where(_Proj.id == _pid))).scalar_one_or_none()
            if _p:
                try:
                    delete_project_physical_files(_pid)
                except Exception:
                    pass
                await db.delete(_p)
                print(f"[cascade-B] 删除关联 project {_pid}")
    except Exception as e:
        print(f"[cascade-B] 异常(不阻塞删任务): {e}")

    # 清理任务物理文件

    # 清理任务物理文件
    clean_task_files(task.id, task.document_path)

    # 删除 task
    await db.delete(task)

    # 级联删除关联的 Project（可能多个）
    if project_ids:
        from app.database.models import Project as _Proj
        for _pid in project_ids:
            _p = (await db.execute(select(_Proj).where(_Proj.id == _pid))).scalar_one_or_none()
            if _p:
                clean_project_files(_pid)
                await db.delete(_p)

    await db.commit()
    return {"message": "任务已删除", "task_id": task_id}


@router.post("/tasks/batch-delete")
async def batch_delete_tasks(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除任务，逐个级联清理 Project + ExperimentRun"""
    task_ids = body.get("task_ids", [])
    if not task_ids:
        raise HTTPException(status_code=400, detail="task_ids 不能为空")

    deleted = 0
    errors = []
    for tid in task_ids:
        q = select(QuestionTask)
        q = q.where(
            QuestionTask.id == tid,
            QuestionTask.user_id == current_user.id,
        )
        task = (await db.execute(q)).scalar_one_or_none()
        if not task:
            errors.append({"task_id": tid, "error": "不存在或无权限"})
            continue

        # 级联清理 ExperimentRun
        try:
            from sqlalchemy import delete as _d
            from app.database.models import ExperimentRun as _ExpRun
            await db.execute(_d(_ExpRun).where(_ExpRun.question_task_id == task.id))
        except Exception as e:
            logger.debug(f"[batch_delete] 清理 ExperimentRun 失败: {e}")

        # 级联 Project（多来源）
        project_ids = set()
        result_meta = task.result or {}
        if isinstance(result_meta, dict) and result_meta.get("project_id"):
            project_ids.add(int(result_meta["project_id"]))

        # 兜底：ExperimentRun 反查
        try:
            from sqlalchemy import delete as _d
            from app.database.models import ExperimentRun as _ExpRun
            _runs = (await db.execute(
                select(_ExpRun).where(_ExpRun.question_task_id == task.id)
            )).scalars().all()
            for _r in _runs:
                if _r.project_id:
                    project_ids.add(int(_r.project_id))
                await db.execute(_d(_ExpRun).where(_ExpRun.id == _r.id))
        except Exception as e:
            logger.debug(f"[batch_delete] 清理 ExperimentRun 失败: {e}")

        if project_ids:
            from app.database.models import Project as _Proj
            p = (await db.execute(select(_Proj).where(_Proj.id == project_id_to_delete))).scalar_one_or_none()
            if p:
                clean_project_files(project_id_to_delete)
                await db.delete(p)

        clean_task_files(task.id, task.document_path)
        await db.delete(task)
        deleted += 1

    await db.commit()
    return {"message": f"已删除 {deleted} 个任务", "deleted": deleted, "errors": errors}


@router.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """对生成结果提交反馈，支持迭代优化"""
    q = select(QuestionTask).where(
        QuestionTask.id == req.task_id,
        QuestionTask.user_id == current_user.id,
    )
    task = (await db.execute(q)).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.feedback = req.feedback
    await db.commit()

    logger.info(f"反馈已提交: task_id={req.task_id}")
    return {"message": "反馈已提交", "task_id": req.task_id}


# ─── 获取我的任务历史 ──────────────────────────────────────────



# ─── 批量导入 Science 125 预置题目 ──────────────────────────────

class BatchImportRequest(BaseModel):
    questions: list[dict] = Field(..., min_length=1, max_length=200)
    skip_existing: bool = True

@router.post("/batch-import")
async def batch_import_questions(
    req: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导入题目（管理员功能），支持 JSON 格式批量写入"""
    imported = 0
    skipped = 0
    errors = []

    # 获取当前最大 question_id
    max_q = select(func.max(ScienceQuestion.question_id))
    max_id = (await db.execute(max_q)).scalar() or 0

    for i, item in enumerate(req.questions):
        try:
            qid = item.get("question_id")
            if not qid:
                max_id += 1
                qid = max_id

            # 检查是否已存在
            if req.skip_existing:
                existing = (await db.execute(
                    select(ScienceQuestion).where(ScienceQuestion.question_id == qid)
                )).scalar_one_or_none()
                if existing:
                    skipped += 1
                    continue

            q = ScienceQuestion(
                question_id=qid,
                title=item.get("title", ""),
                title_en=item.get("title_en"),
                category=item.get("category", "未分类"),
                description=item.get("description", ""),
                keywords=item.get("keywords", []),
                difficulty=item.get("difficulty", "medium"),
                source=item.get("source", "batch_import"),
                is_active=True,
                sort_order=item.get("sort_order", qid),
            )
            db.add(q)
            imported += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)[:200]})

    await db.commit()
    logger.info(f"批量导入完成: user={current_user.id}, imported={imported}, skipped={skipped}, errors={len(errors)}")

    return {
        "message": f"导入完成：新增 {imported} 题，跳过 {skipped} 题",
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }


# ─── 题库题目删除（选取删除 / 批量删除 / 全部清空）────────────────────────────
async def _delete_question_cascade(db, question):
    """物理删除一道题目：连带其下所有 QuestionTask + ExperimentRun"""
    from sqlalchemy import delete as _sqla_delete
    from app.database.models import ExperimentRun as _ExpRun
    tq = select(QuestionTask).where(QuestionTask.question_id == question.question_id)
    tasks = (await db.execute(tq)).scalars().all()
    for t in tasks:
        clean_task_files(t.id, t.document_path)
        try:
            await db.execute(_sqla_delete(_ExpRun).where(_ExpRun.question_task_id == t.id))
        except Exception:
            pass
        await db.delete(t)
    await db.delete(question)


@router.post("/batch-delete")
async def batch_delete_questions(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除题库题目（前端 batchDeleteQuestions 调用）"""
    question_ids = body.get("question_ids", [])
    if not question_ids:
        raise HTTPException(status_code=400, detail="question_ids 不能为空")
    deleted_q = 0
    errors = []
    for qid in question_ids:
        q = select(ScienceQuestion).where(ScienceQuestion.question_id == qid)
        question = (await db.execute(q)).scalar_one_or_none()
        if not question:
            errors.append({"question_id": qid, "error": "题目不存在"})
            continue
        await _delete_question_cascade(db, question)
        deleted_q += 1
    await db.commit()
    return {"message": f"已删除 {deleted_q} 道题目", "deleted": deleted_q, "errors": errors}


@router.delete("/clear-all")
async def clear_all_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """清空全部题库题目"""
    qs = (await db.execute(select(ScienceQuestion))).scalars().all()
    count = 0
    for question in qs:
        await _delete_question_cascade(db, question)
        count += 1
    await db.commit()
    return {"message": f"题库已清空，共删除 {count} 道题目", "deleted": count}


@router.post("/clear-all")
async def clear_all_questions_post(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """兼容 POST 方式清空"""
    qs = (await db.execute(select(ScienceQuestion))).scalars().all()
    count = 0
    for question in qs:
        await _delete_question_cascade(db, question)
        count += 1
    await db.commit()
    return {"message": f"题库已清空，共删除 {count} 道题目", "deleted": count}


# [fix12] 题库题目删除路由（对齐前端 deleteAllQuestions -> DELETE /questions/delete-all）
@router.delete("/delete-all")
async def delete_all_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """清空全部题库题目（含级联清理其下所有 QuestionTask + ExperimentRun）"""
    qs = (await db.execute(select(ScienceQuestion))).scalars().all()
    count = 0
    for question in qs:
        # 复用已有的 _delete_question_cascade（若存在），否则内联
        tq = select(QuestionTask).where(QuestionTask.question_id == question.question_id)
        tasks = (await db.execute(tq)).scalars().all()
        for t in tasks:
            try:
                await _cascade_cleanup_question_task(db, t)
            except Exception:
                pass
            await db.delete(t)
        await db.delete(question)
        count += 1
    await db.commit()
    return {"message": f"题库已清空，共删除 {count} 道题目", "deleted": count}
