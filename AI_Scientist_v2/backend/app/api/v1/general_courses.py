"""智研星枢 - AI 通识课 API

面向"人人都要学一点 AI"的图文微课：
- 课程广场：分类/难度筛选 + 我的完成度
- 学习页：Markdown 正文（复用电子书渲染）+ 随堂自测 + AI 助教
- 内容生产：AI 起草大纲 → 逐节生成正文与自测题（每节一次 LLM 调用，避免长任务超时）

为什么逐节生成而不是"一键生成整门课"：
一门 8 节的课要 8 次大模型调用，同步接口必然超时；逐节生成每步 10-20s，
前端可以按节显示进度、失败只重试该节，也不会因为一次限流丢掉整门课的内容。
"""
import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.qwen_client import call_qwen, QwenError
from app.api.deps import get_current_user, get_current_user_flexible
from app.database.models import (
    User, UserRole, GeneralCourse, GeneralLesson, GeneralProgress,
)
from app.database.session import get_db
from app.services import mode_policy
from app.utils import paths as _paths

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/general", tags=["AI 通识课"])

TEACHER_ROLES = {UserRole.TEACHER, UserRole.RESEARCHER, UserRole.ADMIN}


# ════════════════════════════════════════════════════════════
#  提示词：通识化的硬约束（不是"写得通俗一点"这种空话）
# ════════════════════════════════════════════════════════════
OUTLINE_SYSTEM = """你是面向零基础大众的 AI 通识课主编。你设计的课程要让人愿意学完，
而不是把教材目录搬过来。

要求：
1. 每章解决一个"普通人真的会好奇"的问题，标题用大白话或疑问句，不用术语堆砌；
2. 章节之间要有递进：先建立直觉，再讲原理，最后落到"我能用它做什么"；
3. 每章 6-10 分钟能读完，不要设计成需要预习的硬课；
4. 只输出 JSON，不要解释文字。"""

LESSON_SYSTEM = """你是面向零基础大众的 AI 通识课作者，读者是完全没有计算机背景的成年人。
你写的每一节都要满足下面的硬约束，否则视为不合格：

【必须做到】
1. 开头 2 句话内回答"这一节跟我有什么关系"，用一个读者熟悉的场景切入；
2. 全文至少 2 个生活类比（点外卖、找书、开会、体检报告这类），类比要准确，不能为了通俗而失真；
3. 术语第一次出现时，紧跟一句不超过 25 字的白话解释，写成"（也就是……）"；
4. 至少给出 1 个反直觉结论，并说明为什么直觉会错；
5. 结尾落到"今天就能做的一件事"，必须是具体动作，不要写"多加练习"；
6. 句子以短句为主，单句不超过 40 字；每 2-3 段必须有一个小标题；
7. 不要写代码，不要用公式；必须出现公式时，用一句中文说清它在算什么。

【输出格式】严格 JSON，不要 markdown 代码围栏：
{"summary": "一句话概括本节",
 "minutes": 8,
 "content": "Markdown 正文，700-1100 字，含 3-5 个二级标题",
 "figure": [图解块，1-2 个，用来把本节核心概念画出来，见下],
 "quiz": [{"q": "题干", "options": ["选项1", "选项2", "选项3", "选项4"],
           "answer": 0, "explain": "为什么选它，30 字内"}]}
quiz 必须 3 题，answer 是正确选项下标（0 开始），干扰项要是"听起来合理但确实错了"的选项。

【figure 图解块】每个块是下列四种之一，前端会画成真正的图形，不要写成长段文字：
- 流程：{"kind":"flow","title":"几步走","steps":[{"label":"短标题","desc":"不超过 20 字"}]}（3-5 步）
- 对比：{"kind":"compare","title":"别混淆","left":{"title":"栏目名","items":["短句"]},"right":{"title":"栏目名","items":["短句"]}}（各 2-4 条）
- 要点卡：{"kind":"cards","title":"记住三点","cards":[{"icon":"一个 emoji","title":"短标题","desc":"不超过 30 字"}]}（2-4 张）
- 提示框：{"kind":"callout","tone":"tip|aha|warn","title":"小标题","text":"不超过 60 字"}（挑一个最能点破误会的）
所有文字用中文，宁短勿长。"""

ASK_SYSTEM = """你是这门 AI 通识课的助教。只依据下面提供的本节内容回答，用中文、口语化、短段落。
如果本节没有讲到，就直说"这一节没讲到，但可以这样理解……"，不要编造事实或数字。
回答控制在 300 字以内，必要时用 1 个类比。"""


# ════════════════════════════════════════════════════════════
#  工具
# ════════════════════════════════════════════════════════════
def _extract_json(text: str) -> dict:
    """从模型输出里取出 JSON（容忍 ```json 围栏与前后废话）"""
    if not text:
        return {}
    t = text.strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
        if m:
            t = m.group(1).strip()
    start, end = t.find("{"), t.rfind("}")
    if start >= 0 and end > start:
        t = t[start:end + 1]
    try:
        data = json.loads(t)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _is_owner(course: GeneralCourse, user: User) -> bool:
    return course.author_id == user.id or user.role == UserRole.ADMIN


def _clean_figure(raw) -> list:
    """把模型输出的图解块收敛成前端能安全渲染的结构（丢弃不可用的块，限制长度）"""
    if isinstance(raw, dict):
        raw = [raw]
    out = []
    for b in (raw or [])[:3]:
        if not isinstance(b, dict):
            continue
        kind = str(b.get("kind") or "").strip().lower()
        title = str(b.get("title") or "")[:80]
        if kind == "flow":
            steps = []
            for s in (b.get("steps") or [])[:6]:
                if isinstance(s, dict) and s.get("label"):
                    steps.append({"label": str(s["label"])[:40], "desc": str(s.get("desc") or "")[:80]})
            if len(steps) >= 2:
                out.append({"kind": "flow", "title": title, "steps": steps})
        elif kind == "compare":
            def _side(v):
                if not isinstance(v, dict):
                    return {"title": "", "items": []}
                return {"title": str(v.get("title") or "")[:40],
                        "items": [str(x)[:60] for x in (v.get("items") or [])[:4]]}
            left, right = _side(b.get("left")), _side(b.get("right"))
            if left["items"] and right["items"]:
                out.append({"kind": "compare", "title": title, "left": left, "right": right})
        elif kind == "cards":
            cards = []
            for c in (b.get("cards") or [])[:4]:
                if isinstance(c, dict) and c.get("title"):
                    cards.append({"icon": str(c.get("icon") or "")[:8],
                                  "title": str(c["title"])[:40], "desc": str(c.get("desc") or "")[:80]})
            if len(cards) >= 2:
                out.append({"kind": "cards", "title": title, "cards": cards})
        elif kind == "callout":
            tone = str(b.get("tone") or "tip").strip().lower()
            if tone not in {"tip", "aha", "warn"}:
                tone = "tip"
            text = str(b.get("text") or "")[:160]
            if text:
                out.append({"kind": "callout", "tone": tone, "title": title, "text": text})
    return out


def _course_brief(c: GeneralCourse, done_ids: set[int], total_done: int = 0) -> dict:
    lessons = c.lessons or []
    ready = [l for l in lessons if l.status == "ready"]
    return {
        "id": c.id, "title": c.title, "subtitle": c.subtitle, "emoji": c.emoji,
        "category": c.category, "level": c.level, "summary": c.summary,
        "tags": c.tags or [], "status": c.status,
        "cover_image": c.cover_image or "",
        "lesson_count": len(lessons), "ready_count": len(ready),
        "done_count": sum(1 for l in lessons if l.id in done_ids),
        "minutes_total": sum(int(l.minutes or 0) for l in lessons),
        "created_at": c.created_at.isoformat() if c.created_at else "",
    }


def _lesson_brief(l: GeneralLesson, done_ids: set[int]) -> dict:
    return {
        "id": l.id, "course_id": l.course_id, "order_index": l.order_index,
        "title": l.title, "kicker": l.kicker, "summary": l.summary,
        "minutes": l.minutes, "status": l.status,
        "done": l.id in done_ids,
    }


async def _done_ids(db: AsyncSession, user_id: int, course_id: int | None = None) -> dict[int, str]:
    stmt = select(GeneralProgress).where(GeneralProgress.user_id == user_id)
    if course_id is not None:
        stmt = stmt.where(GeneralProgress.course_id == course_id)
    rows = (await db.execute(stmt)).scalars().all()
    return {r.lesson_id: r.status for r in rows}


async def _course_or_404(db: AsyncSession, course_id: int) -> GeneralCourse:
    stmt = (select(GeneralCourse)
            .options(selectinload(GeneralCourse.lessons))
            .where(GeneralCourse.id == course_id))
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "课程不存在")
    return c


# ════════════════════════════════════════════════════════════
#  课程广场 / 详情
# ════════════════════════════════════════════════════════════
@router.get("/courses")
async def list_courses(q: str = "", category: str = "", level: str = "",
                       mine: bool = False,
                       user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """课程广场。mine=true 只看自己创建的（含草稿）。"""
    stmt = select(GeneralCourse).options(selectinload(GeneralCourse.lessons))
    if mine:
        stmt = stmt.where(GeneralCourse.author_id == user.id)
    else:
        # 草稿只有作者与管理员可见，其他人只看已发布
        if user.role == UserRole.ADMIN:
            pass
        elif user.role in TEACHER_ROLES:
            stmt = stmt.where((GeneralCourse.status == "published")
                              | (GeneralCourse.author_id == user.id))
        else:
            stmt = stmt.where(GeneralCourse.status == "published")
    if category:
        stmt = stmt.where(GeneralCourse.category == category)
    if level:
        stmt = stmt.where(GeneralCourse.level == level)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where((GeneralCourse.title.like(like))
                          | (GeneralCourse.subtitle.like(like))
                          | (GeneralCourse.summary.like(like)))
    stmt = stmt.order_by(GeneralCourse.updated_at.desc())
    rows = (await db.execute(stmt)).scalars().unique().all()

    done = await _done_ids(db, user.id)
    done_ids = {lid for lid, st in done.items() if st == "done"}

    cats = (await db.execute(
        select(GeneralCourse.category, func.count(GeneralCourse.id))
        .where(GeneralCourse.status == "published")
        .group_by(GeneralCourse.category))).all()

    return {
        "items": [_course_brief(c, done_ids) for c in rows],
        "categories": [{"name": n or "未分类", "count": int(k)} for n, k in cats],
        "can_create": user.role in TEACHER_ROLES,
    }


@router.get("/learning-forecast")
async def learning_forecast(user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    """每门课的学习线性预测：近 14 天完成节数外推「预计 X 天后学完」

    整表一次聚合（不按课逐次查库）；未开始的课不给预测，避免噪声。
    """
    from app.services.prediction import linear_forecast
    from datetime import datetime, timedelta, timezone

    courses = (await db.execute(
        select(GeneralCourse.id, GeneralCourse.title)
        .where(GeneralCourse.status == "published"))).all()
    lesson_map = dict((await db.execute(
        select(GeneralLesson.id, GeneralLesson.course_id)
        .where(GeneralLesson.status == "ready"))).all())
    total_by_course: dict[int, int] = {}
    for cid in lesson_map.values():
        total_by_course[cid] = total_by_course.get(cid, 0) + 1
    rows = (await db.execute(
        select(GeneralProgress.lesson_id, GeneralProgress.status, GeneralProgress.percent,
               GeneralProgress.updated_at)
        .where(GeneralProgress.user_id == user.id))).all()

    since = datetime.now(timezone.utc) - timedelta(days=14)
    done_by_course: dict[int, int] = {}
    daily_by_course: dict[int, list[int]] = {}
    for lid, st, pct, upd in rows:
        cid = lesson_map.get(lid)
        if cid is None:
            continue
        if st == "done" or (pct or 0) >= 100:
            done_by_course[cid] = done_by_course.get(cid, 0) + 1
            if upd:
                u = upd if upd.tzinfo else upd.replace(tzinfo=timezone.utc)
                if u >= since:
                    idx = min(13, (u - since).days)
                    series = daily_by_course.setdefault(cid, [0] * 14)
                    series[idx] += 1

    out = []
    for cid, title in courses:
        total = total_by_course.get(cid, 0)
        done = done_by_course.get(cid, 0)
        item = {"course_id": cid, "title": title, "total_lessons": total, "done": done,
                "percent": round(done / total * 100, 1) if total else 0.0,
                "estimated_days_left": None}
        if done > 0 and total > 0 and done < total:
            series = [float(x) for x in daily_by_course.get(cid, [0] * 14)]
            active = sum(1 for x in series if x > 0)
            rate = done / 14.0
            if active >= 3:
                fc = linear_forecast(series)
                if fc["status"] == "ok":
                    rate = max(fc["predicted"], 0.05)
            if rate > 0:
                item["estimated_days_left"] = int((total - done) / rate) + 1
                item["daily_rate"] = round(rate, 2)
        out.append(item)
    return {"ok": True, "items": out}


@router.get("/courses/{course_id}")
async def get_course(course_id: int,
                     user: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    c = await _course_or_404(db, course_id)
    if c.status != "published" and not _is_owner(c, user):
        raise HTTPException(403, "该课程尚未发布")

    prog = await _done_ids(db, user.id, course_id)
    done_ids = {lid for lid, st in prog.items() if st == "done"}
    lessons = [_lesson_brief(l, done_ids) for l in c.lessons]

    # 续学定位：第一门 ready 且未完成的；全完成则回到第一节
    next_id = next((l["id"] for l in lessons if l["status"] == "ready" and not l["done"]), None)
    if next_id is None:
        next_id = next((l["id"] for l in lessons if l["status"] == "ready"), None)

    out = _course_brief(c, done_ids)
    out.update({
        "lessons": lessons,
        "next_lesson_id": next_id,
        "is_owner": _is_owner(c, user),
        "can_edit": _is_owner(c, user),
    })
    return out


# ════════════════════════════════════════════════════════════
#  单节学习
# ════════════════════════════════════════════════════════════
@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: int,
                     user: User = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    l = (await db.execute(
        select(GeneralLesson).where(GeneralLesson.id == lesson_id))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "本节不存在")
    course = await _course_or_404(db, l.course_id)
    if course.status != "published" and not _is_owner(course, user):
        raise HTTPException(403, "该课程尚未发布")

    prog = await _done_ids(db, user.id, l.course_id)
    siblings = [x for x in course.lessons if x.status == "ready"]
    idx = next((i for i, x in enumerate(siblings) if x.id == l.id), -1)
    return {
        "id": l.id, "course_id": l.course_id, "course_title": course.title,
        "title": l.title, "kicker": l.kicker, "summary": l.summary,
        "content": l.content or "", "quiz": l.quiz or [], "minutes": l.minutes,
        "figure": l.figure or [], "cover_image": l.cover_image or "",
        "status": l.status, "done": prog.get(l.id) == "done",
        "prev_id": siblings[idx - 1].id if idx > 0 else None,
        "next_id": siblings[idx + 1].id if 0 <= idx < len(siblings) - 1 else None,
        "total": len(siblings), "index": idx + 1,
    }


@router.post("/lessons/{lesson_id}/progress")
async def report_progress(lesson_id: int, payload: dict,
                          user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    """上报学习进度：percent 0-100；done=true 直接标记完成"""
    l = (await db.execute(
        select(GeneralLesson).where(GeneralLesson.id == lesson_id))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "本节不存在")
    pct = max(0, min(100, int(payload.get("percent") or 0)))
    done = bool(payload.get("done"))
    status = "done" if done or pct >= 100 else "learning"
    if status == "done":
        pct = 100

    row = (await db.execute(select(GeneralProgress).where(
        GeneralProgress.user_id == user.id,
        GeneralProgress.lesson_id == lesson_id))).scalar_one_or_none()
    final_status = status
    if row:
        # 已完成的节不因重看而回退
        if row.status != "done":
            row.status, row.percent = status, pct
        else:
            final_status = "done"
    else:
        db.add(GeneralProgress(user_id=user.id, course_id=l.course_id,
                               lesson_id=lesson_id, status=status, percent=pct))
    await db.commit()

    course = await _course_or_404(db, l.course_id)
    prog = await _done_ids(db, user.id, l.course_id)
    done_count = sum(1 for x in course.lessons if x.status == "ready" and prog.get(x.id) == "done")
    ready_count = sum(1 for x in course.lessons if x.status == "ready")
    return {"ok": True, "status": final_status, "done_count": done_count,
            "ready_count": ready_count,
            "course_percent": int(round(100 * done_count / ready_count)) if ready_count else 0}


@router.post("/lessons/{lesson_id}/ask")
async def ask_ta(lesson_id: int, payload: dict,
                 user: User = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    """AI 助教：只依据本节内容回答，避免跨课瞎编"""
    question = str(payload.get("question") or "").strip()
    if not question:
        raise HTTPException(400, "请先输入问题")
    l = (await db.execute(
        select(GeneralLesson).where(GeneralLesson.id == lesson_id))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "本节不存在")
    body = (l.content or "")[:6000]
    if not body:
        raise HTTPException(409, "本节内容还没生成，暂时不能提问")

    try:
        res = await call_qwen(
            ASK_SYSTEM,
            f"""【本节：{l.title}】
{body}

【学生的提问】{question[:500]}""",
            max_tokens=800, temperature=0.3,
        )
    except QwenError as e:
        raise HTTPException(503, f"AI 助教暂时不可用：{str(e)[:160]}")
    return {"ok": True, "answer": res["content"], "model": res.get("model", "")}


# ════════════════════════════════════════════════════════════
#  AI 内容生产
# ════════════════════════════════════════════════════════════
@router.post("/courses/draft")
async def draft_course(payload: dict,
                       user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """AI 起草一门通识课：只出大纲与章节骨架，正文逐节生成"""
    if user.role not in TEACHER_ROLES:
        raise HTTPException(403, "只有教师可以创建课程")
    topic = str(payload.get("topic") or "").strip()
    if not topic:
        raise HTTPException(400, "请填写课程主题")
    audience = str(payload.get("audience") or "完全零基础的成年人").strip()
    level = str(payload.get("level") or "零基础").strip()
    policy = mode_policy.apply_mode(payload.get("mode"), payload.get("model"))
    gc = policy["general"]
    chapter_count = max(2, min(int(payload.get("chapter_count") or gc["chapter_count"]), 12))

    try:
        res = await call_qwen(
            OUTLINE_SYSTEM + "\n" + policy["directive"],
            f"""课程主题：{topic}
目标读者：{audience}
难度：{level}
章数：{chapter_count}

输出 JSON：
{{"title": "课程名（不超过 20 字，像人话）",
  "subtitle": "一句话说明学完能做什么",
  "emoji": "一个贴合的 emoji",
  "category": "AI 入门 / 应用实践 / 原理素养 / 伦理与社会 之一",
  "level": "{level}",
  "summary": "60 字内课程简介",
  "tags": ["3-5 个标签"],
  "chapters": [{{"title": "章节标题（大白话或疑问句）",
                "kicker": "6-10 字导语",
                "summary": "30 字内本节要解决的问题",
                "minutes": 8}}]}}""",
            max_tokens=2000, temperature=0.6, model=policy["model"],
        )
    except QwenError as e:
        raise HTTPException(503, f"AI 起草失败：{str(e)[:160]}")

    data = _extract_json(res["content"]) or {}
    chapters = [c for c in (data.get("chapters") or []) if isinstance(c, dict)][:chapter_count]
    if not chapters:
        raise HTTPException(502, "AI 没返回可用的大纲，请换个主题或稍后重试")

    course = GeneralCourse(
        title=str(data.get("title") or topic)[:200],
        subtitle=str(data.get("subtitle") or "")[:300],
        emoji=str(data.get("emoji") or "🌱")[:16],
        category=str(data.get("category") or "AI 入门")[:50],
        level=level[:20],
        summary=str(data.get("summary") or "")[:1000],
        tags=[str(t)[:30] for t in (data.get("tags") or [])][:6],
        status="draft", author_id=user.id, lesson_count=len(chapters),
    )
    db.add(course)
    await db.flush()
    for i, ch in enumerate(chapters):
        db.add(GeneralLesson(
            course_id=course.id, order_index=i,
            title=str(ch.get("title") or f"第 {i + 1} 节")[:200],
            kicker=str(ch.get("kicker") or "")[:100],
            summary=str(ch.get("summary") or "")[:1000],
            minutes=max(3, min(int(ch.get("minutes") or 8), 30)),
            status="pending",
        ))
    await db.commit()
    logger.info(f"🌱 通识课草稿 gc{course.id}「{course.title}」{len(chapters)} 节，作者 {user.id}")
    return {"ok": True, "course_id": course.id, "title": course.title,
            "lesson_count": len(chapters), "model": res.get("model", "")}


@router.post("/lessons/{lesson_id}/generate")
async def generate_lesson(lesson_id: int, payload: dict | None = None,
                          user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    """AI 生成单节正文 + 3 道自测题（一次调用，10-20s，失败可单独重试）"""
    l = (await db.execute(
        select(GeneralLesson).where(GeneralLesson.id == lesson_id))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "本节不存在")
    course = await _course_or_404(db, l.course_id)
    if not _is_owner(course, user):
        raise HTTPException(403, "只有课程作者可以生成内容")

    payload = payload or {}
    audience = str(payload.get("audience") or "完全零基础的成年人")[:60]
    style = str(payload.get("style") or "生活化、有画面感")[:40]
    extra = str(payload.get("extra") or "")[:800]
    policy = mode_policy.apply_mode(payload.get("mode"), payload.get("model"))
    gc = policy["general"]
    lesson_system = (
        LESSON_SYSTEM + "\n" + policy["directive"] +
        f"\n【本档尺度】正文控制在 {gc['content_chars']} 字；"
        f"figure 放 {gc['figures']} 个要点类图解（flow/compare/cards）再加 1 个 callout。"
    )

    try:
        res = await call_qwen(
            lesson_system,
            f"""课程：{course.title}（{course.subtitle}）
目标读者：{audience}
风格：{style}
本节标题：{l.title}
本节导语：{l.kicker}
本节要解决的问题：{l.summary}
{('额外要求：' + extra) if extra else ''}

只输出 JSON。""",
            max_tokens=gc["max_tokens"], temperature=0.65, model=policy["model"],
        )
    except QwenError as e:
        raise HTTPException(503, f"AI 生成失败：{str(e)[:160]}")

    data = _extract_json(res["content"]) or {}
    content = str(data.get("content") or "").strip()
    if len(content) < 200:
        raise HTTPException(502, "AI 返回的正文太短，请重试本节")

    quiz = []
    for q in (data.get("quiz") or [])[:5]:
        if not isinstance(q, dict):
            continue
        opts = [str(o)[:120] for o in (q.get("options") or [])[:4]]
        if len(opts) < 2:
            continue
        try:
            ans = int(q.get("answer") or 0)
        except Exception:
            ans = 0
        quiz.append({
            "q": str(q.get("q") or "")[:300], "options": opts,
            "answer": max(0, min(ans, len(opts) - 1)),
            "explain": str(q.get("explain") or "")[:300],
        })

    l.content = content
    l.quiz = quiz
    l.figure = _clean_figure(data.get("figure"))
    l.summary = str(data.get("summary") or l.summary)[:1000]
    try:
        l.minutes = max(3, min(int(data.get("minutes") or l.minutes or 8), 40))
    except Exception:
        pass
    l.status = "ready"
    await db.commit()
    logger.info(f"🌱 通识课 gc{ l.course_id } lesson{l.id} 生成完成 {len(content)} 字 / {len(quiz)} 题 / {len(l.figure)} 个图解")
    return {"ok": True, "lesson_id": l.id, "chars": len(content), "quiz_count": len(quiz),
            "figure_count": len(l.figure),
            "status": "ready", "model": res.get("model", ""),
            "fallback_from": res.get("fallback_from")}


@router.post("/courses/{course_id}/publish")
async def publish_course(course_id: int,
                         user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    c = await _course_or_404(db, course_id)
    if not _is_owner(c, user):
        raise HTTPException(403, "只有课程作者可以发布")
    ready = [l for l in c.lessons if l.status == "ready"]
    if not ready:
        raise HTTPException(409, "还没有任何一节生成完成，不能发布")
    c.status = "published"
    c.lesson_count = len(c.lessons)
    await db.commit()
    return {"ok": True, "status": "published", "ready_count": len(ready)}


@router.delete("/courses/{course_id}")
async def delete_course(course_id: int,
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    c = await _course_or_404(db, course_id)
    if not _is_owner(c, user):
        raise HTTPException(403, "只有课程作者可以删除")
    await db.delete(c)
    await db.commit()
    return {"ok": True}


@router.get("/media/{name}")
async def get_media(name: str, token: str = None,
                    user: User = Depends(get_current_user_flexible)):
    """课程/章节封面插画。<img> 无法带 Authorization 头，所以走 ?token= 查询认证。
    只允许 generated/general 下的扁平图片文件名，禁止路径穿越。"""
    if "/" in name or "\\" in name or ".." in name or not re.match(r"^[\w.-]+\.(png|jpg|jpeg|webp|gif|svg)$", name, re.I):
        raise HTTPException(400, "非法的图片名")
    path = _paths.peek_dir("general", name)
    if not path.is_file():
        raise HTTPException(404, "图片不存在")
    return FileResponse(str(path))
