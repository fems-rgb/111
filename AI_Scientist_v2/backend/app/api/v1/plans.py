"""自由计划中心（Phase D）

一张 plans 表承载四种形态：
- personal   仅本人可见，日常待办
- team       挂在项目上，同项目 owner/管理员可见（沿用既有权限）
- pipeline   items[].agent 对应 AGENT_REGISTRY，可一键 to-pipeline 落成流水线并触发
- auto       AI 自主计划（/plans/ai 生成后直接入库）

约定：items = [{text, due?, agent?, done}]；agent 需为 AGENT_REGISTRY 的键。
"""
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.models import (
    KnowledgeGraph, Plan, Pipeline, Project, User, UserRole,
)
from app.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plans", tags=["自由计划"])

VALID_SCOPES = {"personal", "team", "pipeline", "auto"}


# ═════════════════ Schema ═════════════════

class PlanItem(BaseModel):
    text: str
    due: str | None = None
    agent: str | None = None
    done: bool = False


class PlanCreate(BaseModel):
    title: str
    scope: str = "personal"
    project_id: int | None = None
    items: list[PlanItem] = []
    due_at: str | None = None


class PlanUpdate(BaseModel):
    title: str | None = None
    items: list[PlanItem] | None = None
    status: str | None = None
    due_at: str | None = None
    project_id: int | None = None


class PlanAIRequest(BaseModel):
    topic: str
    scope: str = "personal"        # personal/team/pipeline/auto
    project_id: int | None = None
    mode: str | None = None
    model: str | None = None


# ═════════════════ 工具 ═════════════════

def _plan_dict(p: Plan, project_title: str = "") -> dict:
    return {
        "id": p.id, "owner_id": p.owner_id, "scope": p.scope,
        "project_id": p.project_id, "project_title": project_title,
        "title": p.title, "items": p.items or [], "source": p.source,
        "status": p.status, "due_at": p.due_at.isoformat() if p.due_at else None,
        "pipeline_id": p.pipeline_id or "",
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }


def _parse_due(s: str | None):
    if not s:
        return None
    try:
        # 支持 YYYY-MM-DD / ISO8601
        if len(s) == 10:
            return datetime.fromisoformat(s + "T00:00:00+00:00")
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, f"due_at 时间格式无法解析：{s}")


def _sanitize_items(items: list[PlanItem]) -> list[dict]:
    out: list[dict] = []
    for it in items:
        text = (it.text or "").strip()
        if not text:
            continue
        out.append({
            "text": text[:300],
            "due": (it.due or "")[:32],
            "agent": (it.agent or "")[:32],
            "done": bool(it.done),
        })
    return out


async def _accessible_project(db: AsyncSession, pid: int, user: User) -> Project | None:
    proj = (await db.execute(select(Project).where(Project.id == pid))).scalar_one_or_none()
    if not proj:
        raise HTTPException(404, "项目不存在")
    if proj.owner_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(403, "无权在该团队下建计划")
    return proj


async def _get_plan(db: AsyncSession, plan_id: int, user: User) -> Plan:
    p = (await db.execute(select(Plan).where(Plan.id == plan_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "计划不存在")
    # personal/pipeline/auto 严格 owner；team 走项目权限
    if p.scope != "team":
        if p.owner_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(403, "无权访问该计划")
    else:
        await _accessible_project(db, p.project_id, user)
    return p


def _extract_json(text: str) -> dict:
    if not text:
        return {}
    t = text.strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
        if m:
            t = m.group(1).strip()
    m = re.search(r"\{[\s\S]*\}", t)
    if m:
        t = m.group(0)
    try:
        return json.loads(t)
    except Exception:
        return {}


# ═════════════════ CRUD ═════════════════

@router.get("")
async def list_plans(scope: str | None = None,
                    user: User = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    """按 tab 拉列表：personal/auto/pipeline 只看自己；team 看自己 owner 的项目 + 自己的项目"""
    q = select(Plan)
    if scope:
        if scope not in VALID_SCOPES:
            raise HTTPException(400, "scope 需为 personal/team/pipeline/auto")
        q = q.where(Plan.scope == scope)
    if user.role != UserRole.ADMIN:
        # 非 admin：personal/auto/pipeline 严格 owner；team 也按 owner（团队成员可见由项目权限管）
        q = q.where(Plan.owner_id == user.id)
    rows = (await db.execute(q.order_by(Plan.updated_at.desc()).limit(100))).scalars().all()

    # 关联项目标题（team/pipeline 会用到）
    pids = {p.project_id for p in rows if p.project_id}
    titles: dict[int, str] = {}
    if pids:
        proj_rows = (await db.execute(select(Project).where(Project.id.in_(pids)))).scalars().all()
        titles = {pj.id: pj.title for pj in proj_rows}
    return {"ok": True, "items": [_plan_dict(p, titles.get(p.project_id or 0, "")) for p in rows]}


@router.post("")
async def create_plan(req: PlanCreate, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    if req.scope not in VALID_SCOPES:
        raise HTTPException(400, "scope 需为 personal/team/pipeline/auto")
    if req.scope == "team":
        if not req.project_id:
            raise HTTPException(400, "团队计划必须挂在项目上（project_id 必填）")
        await _accessible_project(db, req.project_id, user)
    plan = Plan(
        owner_id=user.id, scope=req.scope, project_id=req.project_id,
        title=(req.title or "未命名计划")[:200],
        items=_sanitize_items(req.items), source="manual", status="active",
        due_at=_parse_due(req.due_at),
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"ok": True, "plan": _plan_dict(plan)}


@router.get("/{plan_id}")
async def get_plan(plan_id: int, user: User = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    p = await _get_plan(db, plan_id, user)
    return {"ok": True, "plan": _plan_dict(p)}


@router.patch("/{plan_id}")
async def update_plan(plan_id: int, req: PlanUpdate,
                      user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    p = await _get_plan(db, plan_id, user)
    if req.title is not None:
        p.title = req.title[:200]
    if req.items is not None:
        p.items = _sanitize_items(req.items)
    if req.status is not None:
        if req.status not in {"active", "done", "cancelled"}:
            raise HTTPException(400, "status 需为 active/done/cancelled")
        p.status = req.status
    if req.due_at is not None:
        p.due_at = _parse_due(req.due_at)
    if req.project_id is not None:
        await _accessible_project(db, req.project_id, user)
        p.project_id = req.project_id
    await db.commit()
    await db.refresh(p)
    return {"ok": True, "plan": _plan_dict(p)}


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    p = await _get_plan(db, plan_id, user)
    await db.delete(p)
    await db.commit()
    return {"ok": True}


# ═════════════════ AI 生成 ═════════════════

AI_SYSTEM = """你是任务规划助手。给定主题（可能附背景材料），把它拆成 5-8 条**按顺序可执行**的步骤，每步 15 字内，动宾结构、具体不空洞。

严格输出 JSON：
{"title":"计划标题（20字内）","items":[{"text":"步骤","agent":"可选：literature|hypothesis|design|experiment_plan|analysis|writing|review|reflection|knowledge_gap|document_planner","due":"可选：YYYY-MM-DD"}]}

agent 只允许以下取值，其它留空字符串：
knowledge_gap / literature / hypothesis / design / experiment_plan / analysis / writing / review / reflection / document_planner / section_writer / quality_gate / revision / multimodal_enricher
只有当 scope 明确是 pipeline（可执行流水线）时才需要给每步填 agent；其他情况一律留空。"""


@router.post("/ai")
async def ai_generate(req: PlanAIRequest, user: User = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    """AI 生成计划：team/pipeline 场景注入项目研究问题与最新假设"""
    if req.scope not in VALID_SCOPES:
        raise HTTPException(400, "scope 需为 personal/team/pipeline/auto")
    topic = (req.topic or "").strip()
    if len(topic) < 2:
        raise HTTPException(400, "topic 至少 2 字")

    context = ""
    if req.scope in ("team", "pipeline") and req.project_id:
        proj = await _accessible_project(db, req.project_id, user)
        context = f"\n【所属项目】{proj.title}\n【研究问题】{(proj.research_question or '')[:400]}"
        # 最新一条假设，作为 AI 拆解的锚点
        hyp = (await db.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.scope == "project",
                                            KnowledgeGraph.scope_id == str(proj.id))
        )).scalar_one_or_none()
        if hyp and hyp.nodes:
            focus = [n.get("label", "") for n in hyp.nodes[:5] if n.get("label")]
            if focus:
                context += f"\n【已有节点】{'、'.join(focus)}"

    from app.agents.qwen_client import call_qwen
    from app.services import mode_policy
    policy = mode_policy.apply_mode(req.mode, req.model)

    try:
        res = await call_qwen(
            AI_SYSTEM + "\n" + policy["directive"],
            f"scope={req.scope}\n主题：{topic[:200]}{context}\n\n请生成计划 JSON：",
            model=policy["model"], max_tokens=1400, temperature=0.4,
        )
    except Exception as e:
        logger.warning("[plans/ai] %s", e)
        raise HTTPException(503, f"AI 生成失败：{str(e)[:120]}")

    data = _extract_json(res.get("content") or "")
    raw_items = data.get("items") or []
    items: list[dict] = []
    allowed = {"knowledge_gap", "literature", "hypothesis", "design", "experiment_plan",
               "analysis", "writing", "review", "reflection", "document_planner",
               "section_writer", "quality_gate", "revision", "multimodal_enricher"}
    for it in raw_items[:12]:
        if not isinstance(it, dict):
            continue
        text = str(it.get("text") or "").strip()[:120]
        if not text:
            continue
        agent = str(it.get("agent") or "").strip()
        if agent and agent not in allowed:
            agent = ""
        items.append({"text": text, "due": str(it.get("due") or "")[:10],
                       "agent": agent, "done": False})
    if len(items) < 3:
        raise HTTPException(502, "AI 返回的步骤太少，请换个主题或稍后重试")

    plan = Plan(
        owner_id=user.id, scope=req.scope, project_id=req.project_id,
        title=str(data.get("title") or topic)[:200],
        items=items, source="ai", status="active",
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return {"ok": True, "plan": _plan_dict(plan), "model_used": res.get("model") or policy["model"]}


# ═════════════════ 一键转 Pipeline ═════════════════

@router.post("/{plan_id}/to-pipeline")
async def to_pipeline(plan_id: int, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    """把 items[].agent 映射到 AGENT_REGISTRY 落成 Pipeline.steps；若已经有 pipeline_id 则更新 steps"""
    from app.agents.orchestrator import AGENT_REGISTRY

    p = await _get_plan(db, plan_id, user)
    if p.scope not in ("pipeline", "team", "personal", "auto"):
        raise HTTPException(400, "该 scope 不支持转流水线")

    steps: list[dict] = []
    for it in (p.items or []):
        if not isinstance(it, dict):
            continue
        agent = str(it.get("agent") or "").strip()
        if not agent:
            continue
        if agent not in AGENT_REGISTRY:
            raise HTTPException(400,
                                f"步骤「{(it.get('text') or '')[:24]}」的 agent '{agent}' 未注册，"
                                f"可选：{', '.join(AGENT_REGISTRY.keys())}")
        steps.append({
            "agent_name": agent,
            "research_question": str(it.get("text") or p.title)[:500],
        })
    if len(steps) < 2:
        raise HTTPException(400, "可执行的 agent 步骤少于 2，无法落成流水线；请先给步骤指定 agent")

    if p.pipeline_id:
        existing = (await db.execute(
            select(Pipeline).where(Pipeline.id == p.pipeline_id))).scalar_one_or_none()
    else:
        existing = None

    if existing:
        existing.steps = steps
        existing.name = (existing.name or p.title)[:200]
        existing.description = f"由计划 #{p.id} 更新 · {p.title}"[:500]
        pid = existing.id
    else:
        pid = uuid.uuid4().hex[:12]
        row = Pipeline(
            id=pid, user_id=user.id, name=p.title[:200],
            description=f"由计划 #{p.id} 生成 · {p.title}"[:500],
            steps=steps, trigger="manual", status="idle", run_count=0,
        )
        db.add(row)

    p.pipeline_id = pid
    if p.scope == "personal":
        p.scope = "pipeline"
    await db.commit()
    await db.refresh(p)
    return {"ok": True, "pipeline_id": pid, "steps_count": len(steps),
            "plan": _plan_dict(p),
            "run_hint": f"POST /api/v1/automation/{pid}/run 可触发执行"}
