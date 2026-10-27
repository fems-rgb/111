"""通用知识图谱（Phase C）

一张表 + 一个 API 承载四个 scope：
- general   通识课：课程 + 章节标题（LLM 一次抽取）
- syllabus  课程大纲：Course.chapters + syllabus 正文（LLM 一次抽取）
- kb        知识库：用户 Document 标题 + 摘要前 500 字（LLM 一次抽取）
- project   研究项目：Project + AgentTask + Hypothesis 外键直接组装（零 LLM）

前端约定：nodes=[{id,label,group}]，edges=[[source,target,relation]]，节点上限 40。
GET 无缓存时 project 立即组装、其余返回 status="empty"；POST /rebuild 才耗 token。
"""
import asyncio
import json
import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.models import (
    AgentTask, Course, Document, GeneralCourse, GeneralLesson,
    Hypothesis, KnowledgeGraph, Project, User, UserRole,
)
from app.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graphs", tags=["知识图谱"])

VALID_SCOPES = {"general", "syllabus", "kb", "project"}
MAX_NODES = 40


# ═════════════════ 工具 ═════════════════

def _extract_json(text: str) -> dict:
    """从模型输出里取出 JSON（容忍 ```json 围栏与前后废话）"""
    if not text:
        return {}
    t = text.strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
        if m:
            t = m.group(1).strip()
    m = re.search(r"[\{\[][\s\S]*[\}\]]", t)
    if m:
        t = m.group(0)
    try:
        return json.loads(t)
    except Exception:
        return {}


def _sanitize_graph(raw: dict) -> tuple[list[dict], list[list[str]]]:
    """把模型/程序输出的 nodes/edges 收敛成前端契约（≤40 节点，标签 ≤40 字）"""
    nodes: list[dict] = []
    seen: set[str] = set()
    for n in (raw.get("nodes") or [])[:MAX_NODES]:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or "").strip()
        label = str(n.get("label") or "").strip()[:40]
        if not nid or not label or nid in seen:
            continue
        seen.add(nid)
        nodes.append({"id": nid, "label": label,
                      "group": str(n.get("group") or "concept")[:20]})
    ids = set(seen)
    edges: list[list[str]] = []
    for e in (raw.get("edges") or []):
        if isinstance(e, dict):
            s, t, rel = e.get("source"), e.get("target"), e.get("relation") or "related"
        elif isinstance(e, (list, tuple)) and len(e) >= 2:
            s, t = e[0], e[1]
            rel = e[2] if len(e) >= 3 else "related"
        else:
            continue
        s, t = str(s), str(t)
        if s in ids and t in ids and s != t:
            edges.append([s, t, str(rel)[:20]])
    return nodes, edges


GRAPH_SYSTEM = """你是知识结构化助手。给定一份学习/研究材料，你需要抽取其中的核心概念与它们之间的关系，构造一张知识图谱。

严格输出 JSON：{"nodes":[{"id":"简短英文标识","label":"中文显示名","group":"分组名(如 chapter/concept/method/person)"}],"edges":[["源id","目标id","关系词"]]}。
约束：节点不超过 40 个；标签控制在 20 字内；关系词用 2-6 字中文（如"包含""依赖""对比""属于"）；只保留材料里出现过的概念，不要臆造；孤立节点尽量少；id 全局唯一。"""


async def _llm_build(source_text: str, mode: str | None, model: str | None) -> tuple[list[dict], list[list[str]], str]:
    """一次 LLM 抽取，返回 (nodes, edges, model_used)"""
    from app.agents.qwen_client import call_qwen
    from app.services import mode_policy

    policy = mode_policy.apply_mode(mode, model)
    res = await call_qwen(
        GRAPH_SYSTEM + "\n" + policy["directive"],
        f"【材料】\n{source_text[:6000]}\n\n请抽取知识图谱 JSON：",
        model=policy["model"],
        max_tokens=2500, temperature=0.3,
    )
    data = _extract_json(res.get("content") or "")
    nodes, edges = _sanitize_graph(data)
    return nodes, edges, str(res.get("model") or policy["model"])


# ═════════════════ 数据源装配 ═════════════════

async def _general_source(db: AsyncSession, course_id: int) -> str:
    course = (await db.execute(
        select(GeneralCourse).where(GeneralCourse.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(404, "通识课不存在")
    lessons = (await db.execute(
        select(GeneralLesson).where(GeneralLesson.course_id == course_id)
        .order_by(GeneralLesson.order_index))).scalars().all()
    parts = [f"课程：{course.title}（{course.subtitle}）\n摘要：{(course.summary or '')[:400]}"]
    for l in lessons:
        parts.append(f"- 第{l.order_index + 1}节 {l.title}｜导语：{(l.kicker or l.summary or '')[:120]}")
    return "\n".join(parts)


async def _syllabus_source(db: AsyncSession, course_id: int, user: User) -> str:
    course = (await db.execute(
        select(Course).where(Course.id == course_id))).scalar_one_or_none()
    if not course:
        raise HTTPException(404, "课程不存在")
    if course.teacher_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(403, "只有课程负责人可以生成知识图谱")
    parts = [f"课程：{course.title}\n简介：{(course.description or '')[:400]}",
             f"大纲：{(course.syllabus or '')[:1500]}"]
    for ch in (course.chapters or []):
        if not isinstance(ch, dict):
            continue
        title = str(ch.get("title") or "").strip()
        points = ch.get("points") or ch.get("knowledge_points") or []
        if not title:
            continue
        pts = "、".join(str(p)[:30] for p in points[:8]) if isinstance(points, list) else ""
        parts.append(f"章节：{title}\n知识点：{pts}")
    return "\n".join(parts)


async def _kb_source(db: AsyncSession, user: User) -> str:
    docs = (await db.execute(
        select(Document).where(Document.user_id == user.id)
        .order_by(Document.created_at.desc()).limit(20))).scalars().all()
    if not docs:
        return ""
    parts = [f"知识库（{len(docs)} 份资料）"]
    for d in docs:
        summary = (d.summary or d.description or "")[:500]
        parts.append(f"- 文件：{d.filename}\n  摘要：{summary}")
    return "\n".join(parts)


def _project_graph(project: Project, tasks: list[AgentTask],
                   hypotheses: list[Hypothesis]) -> tuple[list[dict], list[list[str]]]:
    """研究项目 → 结构图：零 LLM，纯外键组装"""
    nodes: list[dict] = [{"id": f"P{project.id}", "label": project.title[:30] or "研究项目",
                          "group": "project"}]
    edges: list[list[str]] = []
    for t in tasks[:20]:
        nid = f"T{t.id}"
        nodes.append({"id": nid,
                      "label": f"{t.step_order + 1}. {t.agent_name}"[:30],
                      "group": "task"})
        edges.append([f"P{project.id}", nid, "任务"])
    # 任务按 step_order 串成链，让布局有方向感
    for a, b in zip(tasks[:20], tasks[1:20]):
        edges.append([f"T{a.id}", f"T{b.id}", "顺序"])
    for h in hypotheses[:10]:
        nid = f"H{h.id}"
        label = (h.statement or h.hypo_id or "假设")[:30]
        nodes.append({"id": nid, "label": label, "group": "hypothesis"})
        edges.append([f"P{project.id}", nid, "假设"])
    return _sanitize_graph({"nodes": nodes, "edges": edges})


# ═════════════════ 缓存读写 ═════════════════

async def _load(db: AsyncSession, scope: str, scope_id: str):
    return (await db.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.scope == scope,
                                     KnowledgeGraph.scope_id == scope_id)
    )).scalar_one_or_none()


async def _upsert(db: AsyncSession, scope: str, scope_id: str,
                  nodes: list[dict], edges: list[list[str]],
                  owner_id: int | None, model_used: str) -> KnowledgeGraph:
    row = await _load(db, scope, scope_id)
    status = "ready" if nodes else "empty"
    if row is None:
        row = KnowledgeGraph(scope=scope, scope_id=scope_id)
        db.add(row)
    row.nodes, row.edges, row.status = nodes, edges, status
    row.owner_id = owner_id
    row.model_used = model_used
    await db.commit()
    await db.refresh(row)
    return row


def _to_resp(row: KnowledgeGraph) -> dict:
    return {"ok": True, "scope": row.scope, "scope_id": row.scope_id,
            "status": row.status, "nodes": row.nodes or [], "edges": row.edges or [],
            "model_used": row.model_used or "",
            "updated_at": row.updated_at.isoformat() if row.updated_at else ""}


# ═════════════════ API ═════════════════

@router.get("/{scope}/{scope_id}")
async def get_graph(scope: str, scope_id: str,
                    user: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    """读缓存；project 无缓存时即时组装（零 LLM），其余返回 status=empty 让前端出「AI 生成」按钮"""
    if scope not in VALID_SCOPES:
        raise HTTPException(400, "scope 需为 general / syllabus / kb / project 之一")

    row = await _load(db, scope, scope_id)
    if row is not None:
        return _to_resp(row)

    if scope == "project":
        try:
            pid = int(scope_id)
        except ValueError:
            raise HTTPException(400, "project scope_id 需为整数")
        project = (await db.execute(
            select(Project).where(Project.id == pid))).scalar_one_or_none()
        if not project:
            raise HTTPException(404, "项目不存在")
        if project.owner_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(403, "无权查看该项目")
        tasks = (await db.execute(
            select(AgentTask).where(AgentTask.project_id == pid)
            .order_by(AgentTask.step_order))).scalars().all()
        hyps = (await db.execute(
            select(Hypothesis).where(Hypothesis.project_id == pid))).scalars().all()
        nodes, edges = _project_graph(project, list(tasks), list(hyps))
        row = await _upsert(db, scope, scope_id, nodes, edges, user.id, "")
        return _to_resp(row)

    return {"ok": True, "scope": scope, "scope_id": scope_id,
            "status": "empty", "nodes": [], "edges": [], "model_used": "", "updated_at": ""}


@router.post("/{scope}/{scope_id}/rebuild")
async def rebuild_graph(scope: str, scope_id: str,
                        payload: dict | None = None,
                        user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """重新生成图谱：general/syllabus/kb 走一次 LLM；project 直接外键组装（幂等，不耗 token）"""
    if scope not in VALID_SCOPES:
        raise HTTPException(400, "scope 需为 general / syllabus / kb / project 之一")
    payload = payload or {}
    mode = payload.get("mode")
    model = payload.get("model")

    if scope == "project":
        try:
            pid = int(scope_id)
        except ValueError:
            raise HTTPException(400, "project scope_id 需为整数")
        project = (await db.execute(
            select(Project).where(Project.id == pid))).scalar_one_or_none()
        if not project:
            raise HTTPException(404, "项目不存在")
        if project.owner_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(403, "无权操作该项目")
        tasks = (await db.execute(
            select(AgentTask).where(AgentTask.project_id == pid)
            .order_by(AgentTask.step_order))).scalars().all()
        hyps = (await db.execute(
            select(Hypothesis).where(Hypothesis.project_id == pid))).scalars().all()
        nodes, edges = _project_graph(project, list(tasks), list(hyps))
        row = await _upsert(db, scope, scope_id, nodes, edges, user.id, "")
        return _to_resp(row)

    if scope == "general":
        source = await _general_source(db, int(scope_id))
        owner = user.id
    elif scope == "syllabus":
        source = await _syllabus_source(db, int(scope_id), user)
        owner = user.id
    else:  # kb —— scope_id 约定为 "me" 或 user_id 字符串
        source = await _kb_source(db, user)
        owner = user.id

    if not source.strip():
        raise HTTPException(400, "材料为空，无法生成图谱（先添加章节/资料再试）")

    try:
        nodes, edges, used = await asyncio.wait_for(
            _llm_build(source, mode, model), timeout=90)
    except asyncio.TimeoutError:
        raise HTTPException(504, "AI 抽取超时，请稍后重试")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("[graphs] LLM fail %s/%s: %s", scope, scope_id, e)
        raise HTTPException(503, f"AI 抽取失败：{str(e)[:120]}")

    if not nodes:
        raise HTTPException(502, "AI 没返回可用图谱，请换个模式或稍后重试")

    row = await _upsert(db, scope, scope_id, nodes, edges, owner, used)
    return _to_resp(row)
