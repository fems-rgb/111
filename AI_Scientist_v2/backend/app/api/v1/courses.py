"""智研星枢 - 课程中心 API

角色权限：
- teacher / researcher / admin → 开课、改课、发布、上传课件、AI 生成与刷新
- student → 浏览已发布课程、选课、阅读课件、上报学习进度

路由拆分说明：课程走 /courses/*，课件走 /coursewares/*，
避免 /courses/{course_id} 把 /courses/courseware 当成 id 匹配。
"""
import os
import uuid
import asyncio
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, inspect as sa_inspect
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.database.models import (User, UserRole, Course, CourseStatus, Courseware, Slide,
                                 Enrollment, Document, Project, Pipeline, PipelineRun)
from app.api.deps import get_current_user, get_current_user_flexible
from app.config import settings
from app.security.sanitizer import sanitize_filename
from app.utils import paths
from app.schemas.courses import (CourseCreateRequest, CourseUpdateRequest, GenerateDeckRequest,
                                 AiRefreshRequest, ProgressRequest, OutlineRequest,
                                 CoursewareUpdateRequest, SyncPipelineRequest)
from app.services import ppt_service, course_ai_service, deck_export
from app.services import generate_progress as gp
from app.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["课程中心"])
cw_router = APIRouter(prefix="/coursewares", tags=["课程中心-课件"])

COURSEWARE_EXTS = {".pptx", ".ppt"}
MAX_COURSEWARE_SIZE = 100 * 1024 * 1024
TEACHER_ROLES = {UserRole.TEACHER, UserRole.RESEARCHER, UserRole.ADMIN}


# ════════════════ 权限 & 工具 ════════════════

async def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role not in TEACHER_ROLES:
        raise HTTPException(status_code=403, detail="仅教师/研究员可开设或编辑课程")
    return user


async def _course_or_404(db: AsyncSession, course_id: int) -> Course:
    stmt = (select(Course).where(Course.id == course_id)
            .options(selectinload(Course.teacher), selectinload(Course.coursewares)))
    course = (await db.execute(stmt)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


async def _courseware_or_404(db: AsyncSession, cw_id: int) -> Courseware:
    cw = (await db.execute(select(Courseware).where(Courseware.id == cw_id)
                           .options(selectinload(Courseware.course)))).scalar_one_or_none()
    if not cw:
        raise HTTPException(status_code=404, detail="课件不存在")
    return cw


def _course_out(c: Course, extra: dict | None = None) -> dict:
    """序列化课程。

    teacher / coursewares 是懒加载关系：在 create/update 等未经 selectinload 预加载的
    路径上直接访问会触发异步 IO（MissingGreenlet），因此先查 unloaded 集合，
    未加载则不访问，避免隐式 lazy load。
    """
    unloaded = sa_inspect(c).unloaded
    teacher = None if "teacher" in unloaded else c.teacher
    coursewares = None if "coursewares" in unloaded else c.coursewares
    d = {
        "id": c.id, "title": c.title, "code": c.code, "description": c.description,
        "syllabus": c.syllabus or "", "chapters": c.chapters or [], "domain": c.domain,
        "status": (c.status.value if hasattr(c.status, "value") else str(c.status)),
        "visibility": c.visibility, "cover_emoji": c.cover_emoji,
        "enroll_count": c.enroll_count, "view_count": c.view_count,
        "teacher_id": c.teacher_id,
        "teacher_name": (teacher.display_name or teacher.username) if teacher else "",
        "teacher_institution": (teacher.institution or "") if teacher else "",
        "project_id": c.project_id,
        "courseware_count": len(coursewares) if coursewares is not None else 0,
        "created_at": c.created_at.isoformat() if c.created_at else "",
    }
    return {**d, **(extra or {})}


async def _resolve_material(db: AsyncSession, user: User, sources: dict | None,
                            topic: str, fallback_doc_id: int | None,
                            fallback_project_id: int | None) -> tuple[str, list[dict]]:
    """把多源素材请求归一化并聚合为参考文本（联动核心）"""
    src = dict(sources or {})
    if fallback_doc_id and not src.get("doc_ids"):
        src["doc_ids"] = [fallback_doc_id]
    if fallback_project_id and not src.get("project_id"):
        src["project_id"] = fallback_project_id
    if not any(src.get(k) for k in ("doc_ids", "question_ids", "task_ids", "project_id",
                                    "chat_project_id", "pipeline_run_id", "skill_runs")):
        return "", []
    return await course_ai_service.collect_material(db, user, src, topic=topic)


# ════════════════ 课程浏览 / 管理 ════════════════

@router.get("")
async def list_courses(
    q: str = Query("", max_length=100),
    domain: str = Query("", max_length=50),
    scope: str = Query("all", description="all=已发布 / mine=我教的 / enrolled=我学的"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Course).options(selectinload(Course.teacher), selectinload(Course.coursewares))
    if scope == "mine":
        stmt = stmt.where(Course.teacher_id == user.id)
    elif scope == "enrolled":
        sub = select(Enrollment.course_id).where(Enrollment.student_id == user.id)
        stmt = stmt.where(Course.id.in_(sub))
    else:
        stmt = stmt.where(Course.status == CourseStatus.PUBLISHED, Course.visibility == "public")

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Course.title.ilike(like), Course.description.ilike(like),
                              Course.domain.ilike(like), Course.code.ilike(like)))
    if domain:
        stmt = stmt.where(Course.domain == domain)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    rows = (await db.execute(stmt.order_by(desc(Course.updated_at)).offset(offset).limit(limit))
            ).scalars().unique().all()
    enrolled_ids = set((await db.execute(
        select(Enrollment.course_id).where(Enrollment.student_id == user.id))).scalars().all())

    return {"items": [_course_out(c, {
        "is_enrolled": c.id in enrolled_ids,
        # ★ 列表也要带 is_teacher，否则前端卡片上的“我的课程”徽标、删除按钮永不显示
        "is_teacher": c.teacher_id == user.id or user.role == UserRole.ADMIN,
    }) for c in rows],
            "total": total, "can_teach": user.role in TEACHER_ROLES}


@router.get("/stats")
async def course_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """工作台联动卡片"""
    published = (await db.execute(select(func.count()).select_from(Course)
                                  .where(Course.status == CourseStatus.PUBLISHED))).scalar() or 0
    mine = (await db.execute(select(func.count()).select_from(Course)
                             .where(Course.teacher_id == user.id))).scalar() or 0
    my_enrolled = (await db.execute(select(func.count()).select_from(Enrollment)
                                    .where(Enrollment.student_id == user.id))).scalar() or 0
    total_slides = (await db.execute(select(func.count()).select_from(Slide))).scalar() or 0
    stale_cw = (await db.execute(select(func.count(func.distinct(Slide.courseware_id)))
                                 .where(Slide.risk_score >= 0.4))).scalar() or 0
    ai_made = (await db.execute(select(func.count()).select_from(Courseware)
                                .where(Courseware.source_type == "ai_generated"))).scalar() or 0
    return {"published": published, "my_courses": mine, "my_enrollments": my_enrolled,
            "total_slides": total_slides, "need_update_coursewares": stale_cw,
            "ai_generated_coursewares": ai_made, "can_teach": user.role in TEACHER_ROLES}


@router.get("/materials")
async def material_sources(limit_per: int = Query(30, ge=1, le=100),
                           user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """给前端「素材来源选择器」用：一次拿到可引用的原资料/题目/报告/项目/对话/流水线/技能"""
    docs = (await db.execute(select(Document).where(Document.user_id == user.id)
                             .order_by(desc(Document.created_at)).limit(limit_per))).scalars().all()
    from app.database.models import ScienceQuestion, QuestionTask, CustomSkill
    qs = (await db.execute(select(ScienceQuestion).where(ScienceQuestion.is_active == True)  # noqa: E712
                           .order_by(ScienceQuestion.question_id).limit(limit_per))).scalars().all()
    tasks = (await db.execute(select(QuestionTask).where(QuestionTask.user_id == user.id,
                                                         QuestionTask.status == "completed")
                              .order_by(desc(QuestionTask.id)).limit(limit_per))).scalars().all()
    projs = (await db.execute(select(Project).where(Project.owner_id == user.id)
                              .order_by(desc(Project.id)).limit(limit_per))).scalars().all()
    pipes = (await db.execute(select(Pipeline).where(Pipeline.user_id == user.id)
                              .order_by(desc(Pipeline.last_run)))).scalars().all()
    runs = (await db.execute(select(PipelineRun).where(PipelineRun.pipeline_id.in_(
        [p.id for p in pipes] or ["__none__"])).order_by(desc(PipelineRun.started_at))
        .limit(limit_per))).scalars().all()
    skills = (await db.execute(select(CustomSkill).where(
        (CustomSkill.user_id == user.id) | (CustomSkill.is_public == True))  # noqa: E712
    )).scalars().all()

    from app.api.v1.skills import BUILTIN_SKILLS
    return {
        "documents": [{"id": d.id, "label": d.filename, "ext": d.file_ext,
                       "has_content": bool((d.structured_data or {}).get("content"))} for d in docs],
        "questions": [{"question_id": q.question_id, "label": f"#{q.question_id} {q.title}",
                       "category": q.category} for q in qs],
        "tasks": [{"id": t.id, "label": f"报告 #{t.id} · {t.result.get('title', '') if isinstance(t.result, dict) else ''}"
                                    .strip(" ·"), "question_id": t.question_id} for t in tasks],
        "projects": [{"id": p.id, "label": p.title, "has_chat": True} for p in projs],
        "pipelines": [{"id": p.id, "label": p.name, "steps": len(p.steps or [])} for p in pipes],
        "pipeline_runs": [{"id": r.id, "pipeline_id": r.pipeline_id, "status": r.status,
                           "label": f"{next((p.name for p in pipes if p.id == r.pipeline_id), r.pipeline_id)} · {r.status}"}
                          for r in runs],
        "skills": ([{"id": k, "label": v.get("name", k), "type": "builtin"}
                    for k, v in BUILTIN_SKILLS.items()] +
                   [{"id": f"custom_{s.id}", "label": s.name,
                     "type": "webhook" if (s.webhook_url or "") else "prompt"} for s in skills]),
    }


@router.post("", status_code=201)
async def create_course(req: CourseCreateRequest, user: User = Depends(require_teacher),
                        db: AsyncSession = Depends(get_db)):
    course = Course(teacher_id=user.id, title=req.title, code=req.code,
                    description=req.description, syllabus=req.syllabus, domain=req.domain,
                    cover_emoji=req.cover_emoji or "📖", chapters=req.chapters or [],
                    visibility=req.visibility or "public", project_id=req.project_id)
    db.add(course)
    await db.commit()
    logger.info(f"🎓 课程已创建: #{course.id} {course.title} by {user.username}")
    # 重新带入 eager 加载，避免响应里触发隐式 lazy load
    return _course_out(await _course_or_404(db, course.id))


@router.get("/{course_id}")
async def get_course(course_id: int, user: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    course = await _course_or_404(db, course_id)
    is_teacher = course.teacher_id == user.id or user.role == UserRole.ADMIN
    if course.status != CourseStatus.PUBLISHED and not is_teacher:
        raise HTTPException(status_code=403, detail="课程尚未发布")

    cws = (await db.execute(select(Courseware).where(Courseware.course_id == course_id)
                            .order_by(desc(Courseware.created_at)))).scalars().all()
    enr = (await db.execute(select(Enrollment).where(Enrollment.course_id == course_id,
                                                     Enrollment.student_id == user.id)
                            )).scalar_one_or_none()
    course.view_count = (course.view_count or 0) + 1
    await db.commit()
    return _course_out(course, {
        "is_teacher": is_teacher,
        "coursewares": [{
            "id": w.id, "title": w.title, "source_type": w.source_type,
            "slide_count": w.slide_count, "status": w.status, "version": w.version,
            "parent_id": w.parent_id, "file_size": w.file_size, "read_size_kb": w.read_size_kb,
            "doc_id": w.doc_id, "staleness": w.staleness_report or {},
            "error_message": w.error_message or "",
            "created_at": w.created_at.isoformat() if w.created_at else "",
        } for w in cws],
        "enrollment": None if not enr else {
            "progress": enr.progress, "last_courseware_id": enr.last_courseware_id,
            "last_slide_index": enr.last_slide_index},
    })


@router.patch("/{course_id}")
async def update_course(course_id: int, req: CourseUpdateRequest,
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    course = await _course_or_404(db, course_id)
    if course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可以修改")
    for field in ("title", "code", "description", "syllabus", "domain", "cover_emoji",
                  "chapters", "visibility"):
        val = getattr(req, field, None)
        if val is not None:
            setattr(course, field, val)
    if req.status:
        if req.status not in {s.value for s in CourseStatus}:
            raise HTTPException(status_code=400, detail="非法状态")
        course.status = CourseStatus(req.status)
    await db.commit()
    return _course_out(await _course_or_404(db, course_id))


@router.delete("/{course_id}")
async def delete_course(course_id: int, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    course = await _course_or_404(db, course_id)
    if course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可以删除")
    # 课件电子化会往资料库写一份派生文档，课程删除时一并清掉，
    # 否则资料库会堆一堆无主文档（且其被课件引用时删不掉）
    doc_ids = {w.doc_id for w in (course.coursewares or []) if w.doc_id}
    await db.delete(course)
    await db.flush()
    for did in doc_ids:
        doc = (await db.execute(select(Document).where(Document.id == did))).scalar_one_or_none()
        if doc:
            await db.delete(doc)
    await db.commit()
    return {"ok": True}


# ════════════════ 选课 / 名册 ════════════════

@router.post("/{course_id}/enroll")
async def enroll(course_id: int, user: User = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    course = await _course_or_404(db, course_id)
    if course.status != CourseStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="课程未发布，暂不可选课")
    if course.teacher_id == user.id:
        raise HTTPException(status_code=400, detail="负责人无需选课")
    exist = (await db.execute(select(Enrollment).where(Enrollment.course_id == course_id,
                                                      Enrollment.student_id == user.id)
                              )).scalar_one_or_none()
    if exist:
        return {"ok": True, "already": True, "progress": exist.progress}
    db.add(Enrollment(course_id=course_id, student_id=user.id))
    course.enroll_count = (course.enroll_count or 0) + 1
    await db.commit()
    return {"ok": True, "already": False}


@router.delete("/{course_id}/enroll")
async def unenroll(course_id: int, user: User = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    enr = (await db.execute(select(Enrollment).where(Enrollment.course_id == course_id,
                                                    Enrollment.student_id == user.id)
                            )).scalar_one_or_none()
    if not enr:
        raise HTTPException(status_code=404, detail="未选修该课程")
    course = await _course_or_404(db, course_id)
    course.enroll_count = max(0, (course.enroll_count or 0) - 1)
    await db.delete(enr)
    await db.commit()
    return {"ok": True}


@router.get("/{course_id}/students")
async def list_students(course_id: int, user: User = Depends(require_teacher),
                        db: AsyncSession = Depends(get_db)):
    course = await _course_or_404(db, course_id)
    if course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可查看名册")
    rows = (await db.execute(
        select(Enrollment, User).join(User, User.id == Enrollment.student_id)
        .where(Enrollment.course_id == course_id).order_by(desc(Enrollment.updated_at)))).all()
    return {"items": [{
        "student_id": e.student_id, "name": u.display_name or u.username,
        "institution": u.institution or "", "progress": e.progress,
        "last_slide": e.last_slide_index,
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else "",
    } for e, u in rows], "total": len(rows)}


# ════════════════ 课件电子化（需求 2） ════════════════

@router.post("/{course_id}/courseware", status_code=201)
async def upload_courseware(course_id: int, file: UploadFile = File(...),
                            title: str = Form(default=""),
                            user: User = Depends(require_teacher),
                            db: AsyncSession = Depends(get_db)):
    """上传 PPT → 拆解为电子书（文本层 + 逐页瘦身图 + 懒加载）"""
    course = await _course_or_404(db, course_id)
    if course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可上传课件")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in COURSEWARE_EXTS:
        raise HTTPException(status_code=400,
                            detail="请上传 .pptx 课件（.ppt 请先在 Office 中另存为 .pptx）")
    content = await file.read()
    if len(content) > MAX_COURSEWARE_SIZE:
        raise HTTPException(status_code=400, detail="课件过大，最大 100MB")

    cw = Courseware(course_id=course_id,
                    title=title or sanitize_filename(file.filename or "课件"),
                    source_type="upload", file_size=len(content), status="converting")
    db.add(cw)
    await db.commit()
    await db.refresh(cw)

    saved_name = f"{uuid.uuid4().hex[:12]}{ext}"
    src_dir = os.path.join(settings.UPLOAD_DIR, "courses_src")
    os.makedirs(src_dir, exist_ok=True)
    src_path = os.path.join(src_dir, saved_name)
    with open(src_path, "wb") as f:
        f.write(content)
    cw.source_path = os.path.join("courses_src", saved_name)

    try:
        await _materialize_courseware(db, cw, src_path, creator=user)
    except Exception as e:
        logger.exception("courseware conversion failed")
        cw.status = "failed"
        cw.error_message = str(e)[:500]
        await db.commit()
        raise HTTPException(status_code=500, detail=f"课件电子化失败: {str(e)[:200]}")

    return {"id": cw.id, "title": cw.title, "slide_count": cw.slide_count, "status": cw.status,
            "file_size": cw.file_size, "read_size_kb": cw.read_size_kb, "doc_id": cw.doc_id,
            "optimization": (cw.staleness_report or {}).get("_opt", {})}


# 版式语义字段：Slide 表不新增列，侧挂在 Courseware.staleness_report 里，
# 阅读器与导出 pptx 读回后与文本层合并
_DECK_EXTRA_KEYS = ("layout", "kicker", "lead", "cards", "metrics", "compare",
                    "quote", "quote_by", "takeaway", "key_question", "chapter_no",
                    "detail", "example", "chart", "steps")


def _deck_extras(slides: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for s in slides:
        ex = {k: s.get(k) for k in _DECK_EXTRA_KEYS if s.get(k)}
        if ex:
            out[str(s.get("slide_index"))] = ex
    return out


async def _materialize_courseware(db: AsyncSession, cw: Courseware, src_path: str | None,
                                  slides: list[dict] | None = None,
                                  creator: User | None = None) -> None:
    """slides 落库 + 体积优化统计 + 注册资料库（联动）"""
    if slides is None:
        if not src_path or not os.path.exists(src_path):
            raise ValueError("课件源文件缺失")
        slides = ppt_service.convert_pptx_to_slides(src_path, cw.id)

    db.add_all([Slide(
        courseware_id=cw.id, slide_index=s["slide_index"], title=s.get("title", ""),
        bullets=s.get("bullets", []), notes=s.get("notes", ""), tables=s.get("tables", []),
        image_path=s.get("image_path", ""), image_kb=s.get("image_kb", 0),
        updated_by_ai=bool(s.get("updated_by_ai", False)),
        risk_score=float(s.get("risk_score", 0) or 0),
        risk_category=s.get("risk_category", "") or "",
        ai_reason=s.get("ai_reason", "") or "", ai_suggestion=s.get("ai_suggestion", "") or "",
    ) for s in slides])
    cw.slide_count = len(slides)

    opt = ppt_service.estimate_optimization(cw.file_size or 0, slides)
    cw.read_size_kb = opt["ebook_kb"]
    rep = dict(cw.staleness_report or {})
    rep["_opt"] = opt
    cw.staleness_report = rep
    cw.status = "ready"

    # 联动：课件文本进资料库 → 可被 RAG 检索 / 作为对话附件
    if creator is not None:
        try:
            ebook_md = ppt_service.build_ebook_markdown(slides, cw.title)
            doc = Document(user_id=creator.id, filename=f"{cw.title}.md", saved_name="",
                           file_ext=".md", file_size=len(ebook_md.encode("utf-8")),
                           description=f"课程课件电子化 · course_id={cw.course_id}",
                           summary=ebook_md[:1200],
                           structured_data={"course_id": cw.course_id, "courseware_id": cw.id,
                                            "content": ebook_md[:60000]},
                           parse_status="ok", tags=["courseware", "course"])
            db.add(doc)
            await db.flush()
            cw.doc_id = doc.id
        except Exception as e:
            logger.warning(f"courseware→knowledge 联动注册失败(不影响阅读): {e}")

    await db.commit()
    await db.refresh(cw)


# ════════════════ 阅读端点（coursewares 路由） ════════════════

@cw_router.get("/ai-mine")
async def list_my_ai_coursewares(limit: int = Query(30, ge=1, le=100),
                                user: User = Depends(get_current_user),
                                db: AsyncSession = Depends(get_db)):
    """课件工坊的「我生成过的课件」列表（AI 生成，含导出/阅读链接）

    必须在 /{cw_id} 之前声明，否则 ai-mine 会被当成 cw_id。
    """
    stmt = (select(Courseware)
            .options(selectinload(Courseware.course))
            .join(Course, Course.id == Courseware.course_id)
            .where(Course.teacher_id == user.id, Courseware.source_type == "ai_generated")
            .order_by(desc(Courseware.id)).limit(limit))
    rows = (await db.execute(stmt)).scalars().unique().all()
    return {"items": [{
        "id": c.id, "title": c.title, "course_id": c.course_id, "course_title": c.course.title,
        "slide_count": c.slide_count, "version": c.version, "status": c.status,
        "read_size_kb": c.read_size_kb, "created_at": c.created_at.isoformat() if c.created_at else "",
        "pptx_url": f"/api/v1/coursewares/{c.id}/export/pptx",
        "reader_url": f"/course/{c.course_id}/read/{c.id}",
    } for c in rows], "can_teach": user.role in TEACHER_ROLES}


@cw_router.get("/generate-models")
async def list_generate_models():
    """课件生成可选模型列表（供前端下拉）；必须在 /{cw_id} 之前声明，否则会被当成 cw_id

    默认值跟随后端配置 settings.QWEN_MODEL_NAME。
    """
    default = settings.QWEN_MODEL_NAME
    labels = {
        "qwen-turbo": ("Qwen-Turbo（快速）", "速度快、成本低，适合初稿"),
        "qwen-plus": ("Qwen-Plus（均衡）", "质量与速度均衡，推荐"),
        "qwen-max": ("Qwen-Max（强力）", "质量最高，较慢较贵"),
        "qwen-max-longcontext": ("Qwen-Max 长文", "适合超长大纲/参考资料"),
    }
    items = [{"value": m, "label": labels.get(m, (m, ""))[0],
              "desc": labels.get(m, ("", ""))[1], "is_default": m == default}
             for m in course_ai_service.SUPPORTED_MODELS]
    return {"ok": True, "default": default, "items": items}


@cw_router.get("/{cw_id}")
async def get_courseware_meta(cw_id: int, user: User = Depends(get_current_user),
                              db: AsyncSession = Depends(get_db)):
    """只返回文本层（几十 KB），图片由 /image 懒加载 —— 这是浏览速度的关键"""
    cw = await _courseware_or_404(db, cw_id)
    course = cw.course
    is_teacher = bool(course and (course.teacher_id == user.id or user.role == UserRole.ADMIN))
    if course and course.status != CourseStatus.PUBLISHED and not is_teacher:
        raise HTTPException(status_code=403, detail="课程尚未发布")
    enr = (await db.execute(select(Enrollment).where(Enrollment.course_id == cw.course_id,
                                                    Enrollment.student_id == user.id)
                            )).scalar_one_or_none()
    slides = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id)
                               .order_by(Slide.slide_index))).scalars().all()
    chap_map = (cw.staleness_report or {}).get("_chapter_map") or {}
    extras_map = (cw.staleness_report or {}).get("_deck_extras") or {}
    return {
        "id": cw.id, "title": cw.title, "course_id": cw.course_id,
        "course_title": course.title if course else "",
        "cover_emoji": course.cover_emoji if course else "📖",
        "domain": course.domain if course else "",
        "course_project_id": course.project_id if course else None,
        "version": cw.version, "parent_id": cw.parent_id, "source_type": cw.source_type,
        "status": cw.status, "slide_count": cw.slide_count, "file_size": cw.file_size,
        "read_size_kb": cw.read_size_kb, "doc_id": cw.doc_id,
        "staleness": cw.staleness_report or {}, "optimization": (cw.staleness_report or {}).get("_opt", {}),
        "is_teacher": is_teacher, "enrolled": bool(enr) or is_teacher,
        "resume": {"courseware_id": enr.last_courseware_id, "slide_index": enr.last_slide_index} if enr else None,
        "slides": [{
            "slide_index": s.slide_index, "title": s.title, "bullets": s.bullets or [],
            "notes": s.notes or "", "tables": s.tables or [], "has_image": bool(s.image_path),
            "image_kb": s.image_kb or 0, "risk_score": s.risk_score or 0,
            "risk_category": s.risk_category or "", "ai_reason": s.ai_reason or "",
            "ai_suggestion": s.ai_suggestion or "", "updated_by_ai": bool(s.updated_by_ai),
            "chapter": str(chap_map.get(str(s.slide_index), "")) or "",
            # 版式语义（layout/kicker/lead/cards/metrics/compare）
            **(extras_map.get(str(s.slide_index)) or {}),
        } for s in slides],
    }


@cw_router.get("/{cw_id}/slides/{slide_index}/image")
async def get_slide_image(cw_id: int, slide_index: int,
                          user: User = Depends(get_current_user_flexible),
                          db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id,
                                              Slide.slide_index == slide_index)
                          )).scalar_one_or_none()
    if not s or not s.image_path:
        raise HTTPException(status_code=404, detail="该页无配图")
    # 新产物在 generated/courseware/…，历史数据仍在 uploads/courses/…，resolve 自动兼容
    abs_path = paths.resolve(s.image_path, kind="courseware")
    if not abs_path or not abs_path.is_file():
        raise HTTPException(status_code=404, detail="图片文件缺失")
    return FileResponse(str(abs_path), media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})


def _attachment_header(filename: str, fallback: str) -> dict:
    """中文文件名必须用 RFC 5987 编码，否则浏览器会存成乱码名"""
    from urllib.parse import quote
    ext = filename[filename.rfind("."):] if "." in filename else ""
    return {"Content-Disposition":
            f"attachment; filename={fallback}{ext}; filename*=UTF-8''{quote(filename)}"}


@cw_router.get("/{cw_id}/ebook")
async def download_ebook(cw_id: int, fmt: str = Query("pdf", alias="format"),
                         user: User = Depends(get_current_user_flexible),
                         db: AsyncSession = Depends(get_db)):
    """电子书下载：默认 PDF（可打印、手机可读），也支持 EPUB 与 Markdown

    走 flexible 认证：下载由 <a href> 发起，不会带 Authorization 头，只能靠 ?token=
    """
    cw = await _courseware_or_404(db, cw_id)
    slides = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id)
                               .order_by(Slide.slide_index))).scalars().all()
    extras_map = (cw.staleness_report or {}).get("_deck_extras") or {}
    payload = []
    for s in slides:
        row = {"slide_index": s.slide_index, "title": s.title, "bullets": s.bullets or [],
               "notes": s.notes or "", "tables": s.tables or []}
        # 与 pptx 导出一致：带上版式语义，卡片/对比/数据/金句才会出现在电子书里
        row.update(extras_map.get(str(s.slide_index)) or {})
        payload.append(row)
    md = ppt_service.build_ebook_markdown(payload, cw.title)
    fmt = (fmt or "pdf").lower()
    if fmt == "md":
        return PlainTextResponse(md)

    course_title = cw.course.title if cw.course else ""
    ext = ".epub" if fmt == "epub" else ".pdf"
    out = paths.gen_file("exports", f"cw{cw_id}_v{cw.version}_ebook{ext}")
    if fmt == "epub":
        await asyncio.to_thread(deck_export.build_epub, md, out,
                                title=cw.title, course_title=course_title)
        media = "application/epub+zip"
    else:
        html = deck_export.ebook_html(md, title=cw.title, course_title=course_title,
                                      slide_count=len(slides))
        await asyncio.to_thread(deck_export.html_to_pdf, html, out)
        media = "application/pdf"
    return FileResponse(str(out), media_type=media,
                        headers=_attachment_header(f"《{cw.title}》电子书{ext}", "ebook"))


def _handout_markdown(cw: Courseware, course, rows: list[dict], rep: dict, teacher: bool) -> str:
    """组装讲义 Markdown（不依赖 LLM，本地秒出）

    与电子书的分工：电子书把PPT 读成连贯读物（自己看），讲义是**课堂发放物**：
    按章分组 + 每页要点 + 留白笔记区 + 课后思考题与延伸阅读；
    teacher 版额外给出讲师速记、时长建议与陈旧页警示。
    """
    from datetime import datetime

    ver = "教师版" if teacher else "学生版"
    out: list[str] = [f"# 《{cw.title}》课堂讲义（{ver}）", ""]
    meta_bits = [f"课程：{course.title}" if course else "", f"课件 v{cw.version}",
                 f"共 {len(rows)} 页", datetime.now().strftime("%Y-%m-%d")]
    if course and course.domain:
        meta_bits.append(f"领域：{course.domain}")
    out.append("> " + " · ".join(b for b in meta_bits if b))
    out.append("")

    objectives = [str(o) for o in (rep.get("objectives") or [])]
    if objectives:
        out += ["## 学习目标", ""] + [f"- {o}" for o in objectives] + [""]

    # 按章分组（上传型 PPT 没有章节映射时归入“正文”单章）
    grouped: list[tuple[str, list[dict]]] = []
    for r in rows:
        name = r.get("chapter") or "正文"
        if grouped and grouped[-1][0] == name:
            grouped[-1][1].append(r)
        else:
            grouped.append((name, [r]))

    cn_num = "一二三四五六七八九十"
    out.append("---")
    out.append("")
    for gi, (chap, items) in enumerate(grouped):
        idx_label = cn_num[gi] if gi < 10 else str(gi + 1)
        out.append(f"## {idx_label}、{chap}")
        out.append("")
        for r in items:
            out.append(f"### 第 {r['slide_index'] + 1} 页 · {r['title'] or '（无标题）'}")
            out.append("")
            for b in (r.get("bullets") or []):
                lvl = int((b or {}).get("level", 0) or 0)
                text = str((b or {}).get("text", "")).strip()
                if text:
                    out.append(f"{'- ' if lvl == 0 else '  - '}{text}")
            # 卡片/对比/数据/金句页的正文不在 bullets 里，摊平后补进来
            for lvl, text in ppt_service.layout_points(r):
                out.append(f"{'- ' if lvl == 0 else '  - '}{text}")
            # tables 结构：[表格, ...]，每个表格 = [行, ...]，每行 = [单元格, ...]（首行为表头）
            for tbl in (r.get("tables") or [])[:1]:
                if not tbl or len(tbl) < 2:
                    continue
                header = [str(c or "").replace("|", "｜").strip() for c in tbl[0]]
                if not header:
                    continue
                out.append("")
                out.append("| " + " | ".join(header) + " |")
                out.append("|" + "|".join(["---"] * len(header)) + "|")
                for row in tbl[1:]:
                    cells = [str(c or "").replace("|", "｜").strip() for c in (row or [])][:len(header)]
                    cells += [""] * (len(header) - len(cells))
                    out.append("| " + " | ".join(cells) + " |")
            if teacher:
                if r.get("notes"):
                    out += ["", f"> 🗒️ **讲师速记**：{r['notes']}"]
                if float(r.get("risk_score") or 0) >= 0.4:
                    out += ["", f"> ⚠️ **陈旧风险**：{r.get('risk_category', '')} — "
                            f"{r.get('ai_suggestion') or r.get('ai_reason') or ''}"]
            else:
                out += ["", "📝 笔记：", "", "> ", ""]
            out.append("")
        if teacher:
            out += [f"> ⏱ 本章 {len(items)} 页，建议讲授约 {max(5, len(items) * 3)} 分钟",
                    "","---",""]

    exercises = [str(x) for x in (rep.get("exercises") or [])]
    if exercises:
        out += ["## 课后思考", ""] + [f"{i + 1}. {x}" for i, x in enumerate(exercises)] + [""]
    reading = [str(x) for x in (rep.get("reading") or [])]
    if reading:
        out += ["## 延伸阅读", ""] + [f"- {x}" for x in reading] + [""]
    sources = rep.get("sources_used") or []
    if isinstance(sources, list) and sources:
        out += ["## 本次生成所用的素材来源", ""] + [f"- {s}" for s in sources[:12]] + [""]
    return "\n".join(out)


@cw_router.get("/{cw_id}/handout")
async def download_handout(cw_id: int, audience: str = "student",
                           fmt: str = Query("docx", alias="format"),
                           user: User = Depends(get_current_user_flexible),
                           db: AsyncSession = Depends(get_db)):
    """课堂讲义：默认 Word（.docx），也可 PDF / Markdown

    学生版：要点 + 留白笔记 + 思考题；教师版另附讲透解释、讲师速记、时长建议与陈旧警示。
    同样走 flexible 认证：下载/预览由 <a href> 发起，不带 Authorization 头，只能靠 ?token=
    """
    cw = await _courseware_or_404(db, cw_id)
    course = cw.course
    rep = cw.staleness_report or {}
    chap_map = rep.get("_chapter_map") or {}
    slides = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id)
                               .order_by(Slide.slide_index))).scalars().all()
    if not slides:
        raise HTTPException(status_code=400, detail="课件暂无内容页，无法生成讲义")
    rows = [{"slide_index": s.slide_index, "title": s.title, "bullets": s.bullets or [],
             "notes": s.notes or "", "tables": s.tables or [],
             "risk_score": s.risk_score or 0, "risk_category": s.risk_category or "",
             "ai_reason": s.ai_reason or "", "ai_suggestion": s.ai_suggestion or "",
             "chapter": str(chap_map.get(str(s.slide_index), "")) or ""} for s in slides]
    extras_map = rep.get("_deck_extras") or {}
    for r in rows:
        r.update(extras_map.get(str(r["slide_index"])) or {})
    teacher = str(audience).lower() == "teacher"
    fmt = (fmt or "docx").lower()
    if fmt == "md":
        return PlainTextResponse(_handout_markdown(cw, course, rows, rep, teacher=teacher))

    blocks = deck_export.handout_blocks(
        rows, title=cw.title, course_title=course.title if course else "",
        version=cw.version, teacher=teacher, domain=(course.domain if course else "") or "",
        objectives=[str(o) for o in (rep.get("objectives") or [])],
        exercises=[str(x) for x in (rep.get("exercises") or [])],
        reading=[str(x) for x in (rep.get("reading") or [])],
        sources=[str(x) for x in (rep.get("sources_used") or [])],
    )
    ver = "教师版" if teacher else "学生版"
    if fmt == "pdf":
        html = deck_export.blocks_to_html(blocks, subtitle=f"《{cw.title}》课堂讲义（{ver}）")
        out = paths.gen_file("exports", f"cw{cw_id}_v{cw.version}_handout_{'teacher' if teacher else 'student'}.pdf")
        await asyncio.to_thread(deck_export.html_to_pdf, html, out)
        return FileResponse(str(out), media_type="application/pdf",
                            headers=_attachment_header(f"《{cw.title}》课堂讲义（{ver}）.pdf", "handout"))

    data = await asyncio.to_thread(deck_export.blocks_to_docx, blocks, title=cw.title)
    return Response(content=data,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers=_attachment_header(f"《{cw.title}》课堂讲义（{ver}）.docx", "handout"))


@cw_router.get("/{cw_id}/export/pptx")
async def export_pptx(cw_id: int, user: User = Depends(get_current_user_flexible),
                      db: AsyncSession = Depends(get_db)):
    """反向导出原生 .pptx（课堂投影用，保留老师熟悉的工作流）"""
    cw = await _courseware_or_404(db, cw_id)
    slides = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id)
                               .order_by(Slide.slide_index))).scalars().all()
    rep = cw.staleness_report or {}
    extras_map = rep.get("_deck_extras") or {}
    payload = []
    for s in slides:
        row = {"slide_index": s.slide_index, "title": s.title, "bullets": s.bullets or [],
               "notes": s.notes or "", "tables": s.tables or []}
        # 带上版式语义，导出的 pptx 才能与网页版一致（而不是退回项目符号页）
        row.update(extras_map.get(str(s.slide_index)) or {})
        payload.append(row)
    if not payload:
        raise HTTPException(status_code=400, detail="课件暂无内容页")
    # 导出的 pptx 属于生成文件 → 固定落在 backend/generated/exports/
    out_path = paths.gen_file("exports", f"cw{cw_id}_v{cw.version}.pptx")
    ppt_service.render_pptx(payload, cw.title, str(out_path),
                            audience=str(rep.get("audience") or ""))
    return FileResponse(str(out_path),
                        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        filename=f"{cw.title}_v{cw.version}.pptx")


@cw_router.post("/quick-generate", status_code=202)
async def quick_generate_courseware(req: GenerateDeckRequest,
                                   user: User = Depends(require_teacher),
                                   db: AsyncSession = Depends(get_db)):
    """课件工坊：一个主题直接生成整套课件（异步作业 + 可轮询进度）

    调用后立即返回 job_id，生成在后台跑（一次完整生成要几十到上百秒），
    前端轮询 /coursewares/quick-generate/{job_id} 拿真实进度：第几章、第几页、当前阶段。
    未指定 course_id 时自动创建一门仅自己可见的草稿课程来承载课件。
    """
    course = None
    if req.course_id:
        course = await _course_or_404(db, req.course_id)
        if course.teacher_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="只有课程负责人可生成课件")
    if course is None:
        if not req.create_course:
            raise HTTPException(status_code=400, detail="未指定 course_id")
        course = Course(title=(req.title or req.topic)[:200], code="",
                        description=f"课件工坊自动创建 · 主题：{req.topic}"[:2000],
                        domain=req.domain or "", syllabus=req.syllabus or "",
                        teacher_id=user.id, status=CourseStatus.DRAFT, visibility="private",
                        cover_emoji="📽️")
        db.add(course)
        await db.commit()
        await db.refresh(course)
        logger.info(f"📽️ 课件工坊自动建课: #{course.id} {course.title} by {user.username}")

    payload = (req.model_dump() if hasattr(req, "model_dump") else req.dict())
    payload["course_id"] = course.id  # 后台任务直接用这门课，不再重复建课
    job_id = await gp.new_job(topic=req.topic, course_id=course.id, course_title=course.title,
                              user_id=user.id,
                              chapters_total=max(1, min(int(req.chapter_count or 6), 12)))
    asyncio.create_task(_run_generate_job(job_id, payload, user.id))
    return {"ok": True, "job_id": job_id, "course_id": course.id,
            "course_title": course.title,
            "status_url": f"/api/v1/coursewares/quick-generate/{job_id}"}


@cw_router.get("/quick-generate/{job_id}")
async def quick_generate_status(job_id: str, user: User = Depends(get_current_user)):
    """轮询课件生成进度；status=done 时 result 就是完整生成结果（含 courseware_id）

    先查内存，内存没有则回数据库（服务重启 / 超过内存 TTL 后仍可查到最终结果）。
    """
    snap = await gp.snapshot(job_id)
    if snap is None:
        raise HTTPException(status_code=404,
                            detail="作业记录不存在或已过期，可在「我生成过的课件」里查看结果")
    return {"ok": True, "job_id": job_id, **snap}


@cw_router.post("/quick-generate/{job_id}/cancel")
async def cancel_quick_generate(job_id: str, user: User = Depends(get_current_user)):
    """停止一个正在运行的课件生成作业（可调控）

    只能停自己发起的作业（admin 可停任意）；置位后生成循环会在下一个
    await 边界（通预先一次 LLM 调用之间）停下，作业转 cancelled 终态，可随时重新发起。
    """
    owner = gp.owner_of(job_id)
    if owner is not None and owner != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只能停止自己发起的生成作业")
    if not gp.request_cancel(job_id):
        raise HTTPException(status_code=409, detail="作业不在运行中（已结束或已过期）")
    await gp.update(job_id, stage="cancelling", message="正在停止…（会在当前步骤结束后停下）")
    return {"ok": True, "job_id": job_id, "cancelled": True}


async def _run_generate_job(job_id: str, payload: dict, user_id: int) -> None:
    """后台生成作业：自建 session（请求级 db 已关闭），进度写内存并低频镜像到数据库

    开跑前登记一个取消 Event：前端点「停止」会命中取消端点置位，
    生成循环（大纲/逐章/小结/逐页配图）在每次 await 之间检查，及时抛 GenerationCancelled 停下。
    """
    async def on_progress(stage, percent, message, extra):
        await gp.update(job_id, stage=stage, percent=percent, message=message, **(extra or {}))

    gp.register_cancel(job_id)
    should_cancel = lambda: gp.is_cancelled(job_id)  # noqa: E731
    try:
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
            course = await db.get(Course, int(payload.get("course_id") or 0))
            if not user or not course:
                await gp.update(job_id, status="failed", stage="failed", message="生成失败：会话已失效",
                                error="user or course not found")
                return
            req = GenerateDeckRequest(**payload)
            await gp.update(job_id, stage="start", percent=1, message="开始生成…",
                            course_id=course.id, course_title=course.title)
            out = await _build_deck(db, course, req, user, on_progress=on_progress,
                                    should_cancel=should_cancel)
            out.setdefault("course_id", course.id)
            out["course_title"] = course.title
            await gp.update(job_id, status="done", stage="done", percent=100,
                            message=f"已生成 {out.get('slide_count', 0)} 页课件", result=out)
    except course_ai_service.GenerationCancelled:
        logger.info(f"quick-generate 已手动停止 job={job_id}")
        await gp.update(job_id, status="cancelled", stage="cancelled",
                        message="已停止生成，可调整参数后重新发起")
    except Exception as e:
        logger.exception(f"quick-generate 作业失败 job={job_id}")
        await gp.update(job_id, status="failed", stage="failed",
                        message=f"生成失败：{str(e)[:120]}", error=str(e)[:400])
    finally:
        gp.unregister_cancel(job_id)


@cw_router.post("/{cw_id}/progress")
async def report_progress(cw_id: int, req: ProgressRequest,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cw = await _courseware_or_404(db, cw_id)
    enr = (await db.execute(select(Enrollment).where(Enrollment.course_id == cw.course_id,
                                                    Enrollment.student_id == user.id)
                            )).scalar_one_or_none()
    if not enr:
        return {"ok": False, "reason": "未选修该课程"}
    key = f"cw:{cw_id}:{req.slide_index}"
    read = list(enr.read_slides or [])
    if key not in read:
        read.append(key)
        enr.read_slides = read
    total_cw = (await db.execute(select(func.count(Courseware.id))
                                 .where(Courseware.course_id == cw.course_id))).scalar() or 1
    cw_ids_read = {k.rsplit(":", 1)[0] for k in read}
    # 每份课件读完才算完成：按已读页数比例折算
    slides_per_cw = {}
    for k in read:
        cid = k.rsplit(":", 1)[0]
        slides_per_cw[cid] = slides_per_cw.get(cid, 0) + 1
    totals = dict((await db.execute(
        select(Slide.courseware_id, func.count(Slide.id)).group_by(Slide.courseware_id)
        .where(Slide.courseware_id.in_([int(c.split(":")[1]) for c in cw_ids_read] or [-1]))
    )).all())
    done = 0.0
    for k in cw_ids_read:
        cid = int(k.split(":")[1])
        t = totals.get(cid) or 1
        done += min(1.0, slides_per_cw.get(k, 0) / t)
    enr.progress = max(0, min(100, round(done / max(1, total_cw) * 100)))
    enr.last_courseware_id = cw_id
    enr.last_slide_index = req.slide_index
    await db.commit()
    return {"ok": True, "progress": enr.progress, "slides_read": len(read)}


@cw_router.patch("/{cw_id}/slides")
async def edit_slides(cw_id: int, req: CoursewareUpdateRequest,
                      user: User = Depends(require_teacher), db: AsyncSession = Depends(get_db)):
    """人工微调（AI 稿不是终稿）"""
    cw = await _courseware_or_404(db, cw_id)
    if cw.course and cw.course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可编辑")
    if req.title is not None:
        cw.title = req.title
    if req.slides:
        existing = {s.slide_index: s for s in (await db.execute(
            select(Slide).where(Slide.courseware_id == cw_id))).scalars().all()}
        for it in req.slides:
            try:
                idx = int(it.get("slide_index", -1))
            except Exception:
                continue
            s = existing.get(idx)
            if not s:
                continue
            if "title" in it:
                s.title = str(it["title"])[:300]
            if "bullets" in it and isinstance(it["bullets"], list):
                s.bullets = [{"level": int(b.get("level", 0) or 0),
                              "text": str(b.get("text", ""))[:400]}
                             for b in it["bullets"] if isinstance(b, dict)]
            if "notes" in it:
                s.notes = str(it["notes"])[:4000]
    await db.commit()
    return {"ok": True}


@cw_router.delete("/{cw_id}")
async def delete_courseware(cw_id: int, user: User = Depends(require_teacher),
                            db: AsyncSession = Depends(get_db)):
    cw = await _courseware_or_404(db, cw_id)
    if cw.course and cw.course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可删除")
    # 教师上传的原件仍在 uploads/，派生渲染图在 generated/courseware/，导出的 pptx 在
    # generated/exports/，三处都清掉，避免删完还留着磁盘垃圾
    rows = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id))).scalars().all()
    targets = [cw.source_path] + [f"courseware/c{cw.id // 100 or 1}/cw{cw.id}/s{s.slide_index:03d}.jpg"
                                  for s in rows]
    for stored in targets:
        if not stored:
            continue
        p = paths.resolve(stored, kind="courseware")
        try:
            if p and p.is_file():
                os.remove(p)
        except OSError:
            pass
    # 图目录删空后一并移除，避免每删一份课件就留下一串空目录
    try:
        cw_dir = paths.GENERATED_ROOT / paths.rel("courseware", f"c{cw.id // 100 or 1}", f"cw{cw.id}")
        for d in (cw_dir, cw_dir.parent):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
    except OSError as e:
        logger.debug(f"slide dir cleanup skipped: {e}")
    # 导出缓存文件名固定为 cw{id}_v{version}.pptx，按前缀清理（历史版本也一并清）
    try:
        exports_dir = paths.gen_dir("exports")
        for f in exports_dir.glob(f"cw{cw_id}_v*.pptx"):
            f.unlink(missing_ok=True)
    except OSError as e:
        logger.debug(f"export cleanup skipped: {e}")
    # 联动生成的「课件电子化」文档也要删，否则知识库里会不断堆积已删课件的孤儿文档。
    # 顺序很重要：coursewares.doc_id 外键指向 documents，必须先删课件行再删文档
    doc_id = cw.doc_id
    await db.delete(cw)
    await db.flush()
    if doc_id:
        doc = (await db.execute(select(Document).where(Document.id == doc_id)
                                )).scalar_one_or_none()
        if doc:
            await db.delete(doc)
    await db.commit()
    return {"ok": True}


@cw_router.get("/{cw_id}/versions")
async def list_versions(cw_id: int, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """版本链：原始版 → AI 更新版，供老师对比/回退"""
    cw = await _courseware_or_404(db, cw_id)
    root_id, guard = cw.parent_id or cw.id, 0
    while guard < 20:
        parent = (await db.execute(select(Courseware).where(
            Courseware.id == root_id))).scalar_one_or_none()
        if not parent or not parent.parent_id:
            break
        root_id, guard = parent.parent_id, guard + 1
    kin, seen, frontier = [], set(), [root_id]
    while frontier:
        rows = (await db.execute(select(Courseware).where(
            Courseware.parent_id.in_(frontier) | Courseware.id.in_(frontier)))).scalars().all()
        frontier = []
        for k in rows:
            if k.id not in seen:
                seen.add(k.id)
                kin.append(k)
                frontier.append(k.id)
    kin = sorted(kin, key=lambda x: (x.version, x.id))
    return {"items": [{"id": k.id, "title": k.title, "version": k.version,
                       "source_type": k.source_type, "slide_count": k.slide_count,
                       "parent_id": k.parent_id, "is_current": k.id == cw_id,
                       "created_at": k.created_at.isoformat() if k.created_at else ""} for k in kin]}


# ════════════════ AI：陈旧度体检 + 自动更新（需求 3） ════════════════

@cw_router.post("/{cw_id}/staleness-scan")
async def staleness_scan(cw_id: int, user: User = Depends(require_teacher),
                         db: AsyncSession = Depends(get_db)):
    cw = await _courseware_or_404(db, cw_id)
    course = cw.course
    slides = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id)
                               .order_by(Slide.slide_index))).scalars().all()
    if not slides:
        raise HTTPException(status_code=400, detail="课件暂无内容页")
    payload = [{"slide_index": s.slide_index, "title": s.title, "bullets": s.bullets or []} for s in slides]
    report = await course_ai_service.scan_staleness(
        payload, course_title=course.title if course else cw.title,
        domain=course.domain if course else "", project_id=course.project_id if course else None)

    by_idx = {i["slide_index"]: i for i in report["items"]}
    for s in slides:
        item = by_idx.get(s.slide_index, {})
        s.risk_score = float(item.get("risk_score", 0) or 0)
        s.risk_category = item.get("category", "") or ""
        s.ai_reason = item.get("reason", "") or ""
        s.ai_suggestion = item.get("suggestion", "") or ""
    rep = dict(cw.staleness_report or {})
    rep["summary"] = report["summary"]
    rep["categories"] = report["summary"].get("categories", {})
    rep["cost"] = report.get("cost", 0)
    from datetime import datetime
    rep["scanned_at"] = datetime.now().isoformat(timespec="seconds")
    cw.staleness_report = rep
    await db.commit()
    return {"ok": True, "summary": report["summary"], "items": report["items"],
            "cost": report.get("cost", 0)}


@cw_router.post("/{cw_id}/ai-refresh")
async def ai_refresh(cw_id: int, req: AiRefreshRequest,
                     user: User = Depends(require_teacher), db: AsyncSession = Depends(get_db)):
    """把陈旧页重写 → 生成新版本（原版保留，可对比）；支持叠加多源素材"""
    cw = await _courseware_or_404(db, cw_id)
    course = cw.course
    slides = (await db.execute(select(Slide).where(Slide.courseware_id == cw_id)
                               .order_by(Slide.slide_index))).scalars().all()
    old = [{"slide_index": s.slide_index, "title": s.title, "bullets": s.bullets or [],
            "notes": s.notes or "", "tables": s.tables or [], "image_path": s.image_path,
            "image_kb": s.image_kb, "risk_score": s.risk_score or 0,
            "risk_category": s.risk_category or "", "ai_reason": s.ai_reason or "",
            "ai_suggestion": s.ai_suggestion or ""} for s in slides]
    # 旧版式语义与章节映射要一并带进改写链路，否则新版本会退回项目符号页、讲义丢分组
    rep_old = cw.staleness_report or {}
    extras_old = rep_old.get("_deck_extras") or {}
    chap_old = rep_old.get("_chapter_map") or {}
    for r in old:
        r.update(extras_old.get(str(r["slide_index"])) or {})
        if not r.get("chapter"):
            r["chapter"] = str(chap_old.get(str(r["slide_index"]), ""))

    if not any((s.risk_score or 0) > 0 for s in slides):
        report = await course_ai_service.scan_staleness(
            [{"slide_index": s["slide_index"], "title": s["title"], "bullets": s["bullets"]} for s in old],
            course_title=course.title if course else cw.title,
            domain=course.domain if course else "")
        report_items = report["items"]
        by_idx = {i["slide_index"]: i for i in report_items}
        for s, src in zip(slides, old):
            item = by_idx.get(s.slide_index, {})
            s.risk_score = float(item.get("risk_score", 0) or 0)
            s.risk_category = item.get("category", "") or ""
            s.ai_reason = item.get("reason", "") or ""
            s.ai_suggestion = item.get("suggestion", "") or ""
            src.update({"risk_score": s.risk_score, "risk_category": s.risk_category,
                        "ai_reason": s.ai_reason, "ai_suggestion": s.ai_suggestion})
        await db.commit()
    else:
        report_items = [{"slide_index": s.slide_index, "risk_score": s.risk_score or 0,
                         "category": s.risk_category or "", "reason": s.ai_reason or "",
                         "suggestion": s.ai_suggestion or ""} for s in slides]

    if req.slide_indexes:
        wanted = set(req.slide_indexes)
        report_items = [i for i in report_items if i["slide_index"] in wanted]

    # 联动：原资料/科学问题/报告/项目/对话/流水线/技能 都可作为更新依据
    material, provenance = await _resolve_material(
        db, user, req.sources, cw.title, req.reference_doc_id,
        course.project_id if course else None)
    extra = "\n\n".join(x for x in [req.extra_context, material] if x)

    new_slides, usage = await course_ai_service.refresh_slides(
        old, report_items, course_title=course.title if course else cw.title,
        domain=course.domain if course else "", extra_context=extra,
        project_id=course.project_id if course else None)

    if usage.get("updated", 0) == 0:
        return {"ok": True, "updated": 0, "new_courseware_id": None,
                "message": "没有需要更新的页面（或 AI 未返回可用结果）",
                "cost": usage.get("cost", 0), "sources_used": provenance}

    new_cw = Courseware(course_id=cw.course_id, title=req.title or f"{cw.title} · AI 更新版",
                        source_type="ai_generated", status="converting",
                        version=cw.version + 1, parent_id=cw.id, file_size=0)
    db.add(new_cw)
    await db.commit()
    await db.refresh(new_cw)
    rel, abs_dir = ppt_service._slides_dir(new_cw.id)
    for s in new_slides:
        if s.get("updated_by_ai"):
            # 改动页重绘配图；未改动页沿用原图
            s["image_path"] = ""
            s["image_kb"] = 0
    for s in new_slides:
        if s.get("updated_by_ai"):
            try:
                path, kb = ppt_service._render_slide_only(
                    s, abs_dir, rel, f"s{s['slide_index']:03d}.jpg",
                    deck_title=new_cw.title,
                    audience=(cw.staleness_report or {}).get("audience") or "")
                s["image_path"], s["image_kb"] = path, kb
            except Exception as e:
                logger.debug(f"refresh slide render skipped: {e}")
    await _materialize_courseware(db, new_cw, None, slides=new_slides, creator=user)
    rep = dict(new_cw.staleness_report or {})
    rep["sources_used"] = provenance
    rep["refreshed_from"] = cw_id
    # 新版本同样要带版式语义与章节映射，否则阅读器/导出会退回项目符号页
    rep["_deck_extras"] = _deck_extras(new_slides)
    rep["_chapter_map"] = {str(s["slide_index"]): s.get("chapter", "")
                           for s in new_slides if s.get("chapter")}
    rep["audience"] = (cw.staleness_report or {}).get("audience", "")
    new_cw.staleness_report = rep
    await db.commit()
    return {"ok": True, "updated": usage["updated"], "new_courseware_id": new_cw.id,
            "version": new_cw.version, "cost": usage.get("cost", 0),
            "tokens": usage.get("tokens", {}), "slide_count": new_cw.slide_count,
            "sources_used": provenance}


# ════════════════ AI：快速做课件（需求 4，多源素材驱动） ════════════════

async def _build_deck(db: AsyncSession, course: Course, req: GenerateDeckRequest,
                      user: User, on_progress=None, should_cancel=None) -> dict:
    """生成整套课件（课程内生成与课件工坊一键生成共用）

    on_progress(stage, percent, message, extra)：素材聚合 → 大纲 → 逐章 → 逐页配图 → 落库，
    课件工坊用它驱动前端进度条；课程内同步生成不传即可。
    """
    async def _emit(stage, percent, message, **extra):
        if on_progress:
            try:
                await on_progress(stage, int(percent), str(message), extra)
            except Exception as e:  # 上报失败不能影响生成
                logger.debug(f"deck progress emit skipped: {e}")

    await _emit("material", 3, "正在聚合多源素材（资料/问题/对话/流水线/技能）…")
    material, provenance = await _resolve_material(
        db, user, req.sources, req.topic, req.reference_doc_id, req.project_id or course.project_id)

    slides, meta = await course_ai_service.generate_deck(
        topic=req.topic, syllabus=req.syllabus or course.syllabus or "",
        chapter_count=req.chapter_count, slides_per_chapter=req.slides_per_chapter,
        style=req.style, audience=req.audience,
        domain=req.domain or course.domain or "", reference_material=material,
        project_id=req.project_id or course.project_id, on_progress=on_progress,
        model=req.model, should_cancel=should_cancel)

    if not slides:
        raise HTTPException(status_code=500, detail="AI 未返回可用课件内容，请调整大纲后重试")

    if not req.auto_save:
        return {"ok": True, "saved": False, "slides": slides, "chapters": meta.get("chapters", []),
                "cost": meta.get("cost", 0), "sources_used": provenance}

    cw = Courseware(course_id=course.id, title=req.title or f"{req.topic} · AI 生成课件",
                    source_type="ai_generated", status="converting", slide_count=len(slides))
    db.add(cw)
    await db.commit()
    await db.refresh(cw)
    rel, abs_dir = ppt_service._slides_dir(cw.id)
    total = len(slides)
    for idx, s in enumerate(slides):
        if should_cancel and should_cancel():
            raise course_ai_service.GenerationCancelled()
        try:
            path, kb = ppt_service._render_slide_only(s, abs_dir, rel, f"s{s['slide_index']:03d}.jpg",
                                                      deck_title=cw.title, audience=req.audience)
            s["image_path"], s["image_kb"] = path, kb
        except Exception as e:
            logger.debug(f"ai slide render skipped: {e}")
        if idx % 2 == 0 or idx == total - 1:  # 本地图渲染很快，隔页刷新避免写太密
            await _emit("render", 96 + int(3 * (idx + 1) / max(1, total)),
                        f"正在绘制第 {idx + 1}/{total} 页配图…",
                        slides_done=idx + 1, slides_total=total)
    if meta.get("chapters"):
        course.chapters = meta["chapters"]
    await _emit("persist", 99, "正在写入课件库、渲染电子书并归档资料…",
                slides_done=total, slides_total=total)
    # Slide 表没有 chapter 列（避免动迁移），这里侧挂一份 index → 章名 映射，
    # 由 /coursewares/{id} 读回后附到每页，详情页与阅读器就能按章分组
    chap_map = {str(s["slide_index"]): s.get("chapter", "") for s in slides if s.get("chapter")}
    extras_map = _deck_extras(slides)
    await _materialize_courseware(db, cw, None, slides=slides, creator=user)
    rep = dict(cw.staleness_report or {})
    rep["sources_used"] = provenance
    rep["_chapter_map"] = chap_map
    rep["_deck_extras"] = extras_map
    rep["audience"] = req.audience
    rep["exercises"] = meta.get("exercises", [])
    rep["reading"] = meta.get("reading", [])
    rep["objectives"] = meta.get("objectives", [])
    cw.staleness_report = rep
    await db.commit()
    logger.info(f"🎓 AI 生成课件 cw{cw.id} {len(slides)}页 (cost ¥{meta.get('cost', 0):.4f}, "
                f"素材源 {len(provenance)} 个)")
    return {"ok": True, "saved": True, "course_id": course.id, "courseware_id": cw.id,
            "slide_count": cw.slide_count, "chapters": meta.get("chapters", []),
            "cost": meta.get("cost", 0), "tokens": meta.get("tokens", {}), "version": cw.version,
            "model": meta.get("model", ""),
            "title": cw.title, "exercises": meta.get("exercises", []),
            "reading": meta.get("reading", []),
            "pptx_url": f"/api/v1/coursewares/{cw.id}/export/pptx",
            "ebook_url": f"/api/v1/coursewares/{cw.id}/ebook",
            "handout_url": f"/api/v1/coursewares/{cw.id}/handout",
            "reader_url": f"/course/{course.id}/read/{cw.id}", "sources_used": provenance}


@router.post("/{course_id}/sync-from-pipeline")
async def sync_from_pipeline(course_id: int, req: SyncPipelineRequest,
                             user: User = Depends(require_teacher),
                             db: AsyncSession = Depends(get_db)):
    """走研究流水线：把流水线产出转成讲义（可叠加技能产出）"""
    course = await _course_or_404(db, course_id)
    if course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="只有课程负责人可执行")
    pipe = (await db.execute(select(Pipeline).where(Pipeline.id == req.pipeline_id,
                                                    Pipeline.user_id == user.id)
                             )).scalar_one_or_none()
    if not pipe:
        raise HTTPException(status_code=404, detail="流水线不存在或无权访问")

    run = None
    if req.run_id:
        run = (await db.execute(select(PipelineRun).where(PipelineRun.id == req.run_id,
                                                          PipelineRun.pipeline_id == pipe.id)
                                )).scalar_one_or_none()
    if not run:
        run = (await db.execute(select(PipelineRun).where(
            PipelineRun.pipeline_id == pipe.id, PipelineRun.status == "completed")
            .order_by(desc(PipelineRun.started_at)).limit(1))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=400,
                            detail="该流水线暂无成功运行记录，请先在自动化模块运行一次（或提供 run_id）")

    topic = req.topic or pipe.name
    material, provenance = await _resolve_material(
        db, user, {"pipeline_run_id": run.id, "skill_runs": req.skill_runs or [],
                   "project_id": course.project_id}, topic, None, None)
    if not material:
        raise HTTPException(status_code=400, detail="流水线运行结果为空，无法生成讲义")

    slides, meta = await course_ai_service.generate_deck(
        topic=topic, syllabus=course.syllabus or pipe.description or "",
        chapter_count=req.chapter_count, slides_per_chapter=req.slides_per_chapter,
        style="研究进展", audience="本科生", domain=course.domain or "",
        reference_material=material, project_id=course.project_id)
    if not slides:
        raise HTTPException(status_code=500, detail="AI 未能从流水线产出转成课件")

    cw = Courseware(course_id=course_id,
                    title=req.title or f"{topic} · 流水线产出讲义",
                    source_type="ai_generated", status="converting", slide_count=len(slides))
    db.add(cw)
    await db.commit()
    await db.refresh(cw)
    cw.title = req.title or f"{topic} · 流水线产出讲义 (源 run {str(run.id)[:8]})"
    rel, abs_dir = ppt_service._slides_dir(cw.id)
    for s in slides:
        try:
            path, kb = ppt_service._render_slide_only(s, abs_dir, rel, f"s{s['slide_index']:03d}.jpg")
            s["image_path"], s["image_kb"] = path, kb
        except Exception:
            pass
    if meta.get("chapters"):
        course.chapters = meta["chapters"]
    await _materialize_courseware(db, cw, None, slides=slides, creator=user)
    rep = dict(cw.staleness_report or {})
    rep.update({"pipeline_id": pipe.id, "run_id": run.id, "sources_used": provenance,
                "_deck_extras": _deck_extras(slides), "audience": "本科生"})
    cw.staleness_report = rep
    await db.commit()
    return {"ok": True, "courseware_id": cw.id, "slide_count": cw.slide_count,
            "pipeline": {"id": pipe.id, "name": pipe.name}, "run_id": run.id,
            "chapters": meta.get("chapters", []), "cost": meta.get("cost", 0),
            "sources_used": provenance, "title": cw.title}


@router.post("/ai/outline")
async def ai_outline(req: OutlineRequest, user: User = Depends(require_teacher),
                     db: AsyncSession = Depends(get_db)):
    """粘贴大纲/讲义文本（也可叠加素材）→ 自动结构化章节，开课辅助"""
    material, provenance = await _resolve_material(db, user, req.sources, "", None, None)
    text = req.text + (("\n\n" + material) if material else "")
    data, usage = await course_ai_service.outline_from_syllabus(text, req.domain)
    return {"ok": True, "title": data.get("title", ""), "domain": data.get("domain", ""),
            "chapters": data.get("chapters", []), "cost": usage.get("cost", 0),
            "sources_used": provenance}
