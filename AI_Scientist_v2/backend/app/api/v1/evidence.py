"""智研星枢 - 证据库管理API（Evidence CRUD + 假设关联）"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from app.database.session import get_db
from app.database.models import User, Hypothesis, Project
from app.api.deps import get_current_user
from app.security.prompt_guard import prompt_guard

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evidence", tags=["证据库"])


# ── Pydantic Schemas ──────────────────────────────

class EvidenceCreate(BaseModel):
    hypothesis_id: int = Field(..., description="关联假设ID")
    content: str = Field(..., min_length=1, max_length=50000, description="证据内容")
    source: str = Field(default="", max_length=500, description="证据来源（文献/实验/访谈等）")
    evidence_type: str = Field(default="empirical", description="类型: empirical/theoretical/methodological/statistical")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="证据强度 0-1")
    tags: list[str] = Field(default_factory=list)


class EvidenceUpdate(BaseModel):
    content: str | None = Field(None, min_length=1, max_length=50000)
    source: str | None = Field(None, max_length=500)
    evidence_type: str | None = None
    strength: float | None = Field(None, ge=0.0, le=1.0)
    tags: list[str] | None = None


class EvidenceResponse(BaseModel):
    id: str
    hypothesis_id: int
    content: str
    source: str
    evidence_type: str
    strength: float
    tags: list[str]
    created_at: str


# ── Helper: 解析 evidence_chain JSON ──────────────

def _parse_chain(raw: str | None) -> list[dict]:
    """安全解析 evidence_chain Text 字段为列表"""
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _serialize_chain(chain: list[dict]) -> str:
    return json.dumps(chain, ensure_ascii=False)


async def _get_hypo_or_404(
    hypo_id: int, user: User, db: AsyncSession
) -> Hypothesis:
    """获取假设并校验权限（通过 project ownership）"""
    stmt = select(Hypothesis).where(Hypothesis.id == hypo_id)
    hypo = (await db.execute(stmt)).scalar_one_or_none()
    if not hypo:
        raise HTTPException(status_code=404, detail="假设不存在")
    # 校验项目归属
    proj = (await db.execute(
        select(Project).where(Project.id == hypo.project_id)
    )).scalar_one_or_none()
    if not proj or proj.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作该假设的证据")
    return hypo


# ── API Endpoints ─────────────────────────────────

@router.get("", response_model=list[EvidenceResponse])
async def list_evidence(
    hypothesis_id: int = Query(..., description="假设ID"),
    evidence_type: str = Query(default="", description="按类型过滤"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出某假设下的所有证据"""
    hypo = await _get_hypo_or_404(hypothesis_id, user, db)
    chain = _parse_chain(hypo.evidence_chain)

    if evidence_type:
        chain = [e for e in chain if e.get("evidence_type") == evidence_type]

    return [
        {
            "id": e.get("id", ""),
            "hypothesis_id": hypothesis_id,
            "content": e.get("content", ""),
            "source": e.get("source", ""),
            "evidence_type": e.get("evidence_type", "empirical"),
            "strength": e.get("strength", 0.5),
            "tags": e.get("tags", []),
            "created_at": e.get("created_at", ""),
        }
        for e in chain
    ]


@router.post("", response_model=EvidenceResponse)
async def create_evidence(
    body: EvidenceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为假设添加一条新证据"""
    # 安全检查
    is_safe, reason = prompt_guard.check(body.content)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"安全检测未通过: {reason}")

    hypo = await _get_hypo_or_404(body.hypothesis_id, user, db)
    chain = _parse_chain(hypo.evidence_chain)

    import uuid
    from datetime import datetime, timezone
    evidence_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()

    entry = {
        "id": evidence_id,
        "content": body.content,
        "source": body.source,
        "evidence_type": body.evidence_type,
        "strength": body.strength,
        "tags": body.tags,
        "created_at": now,
    }
    chain.append(entry)

    hypo.evidence_chain = _serialize_chain(chain)
    await db.commit()

    logger.info(f"[Evidence] Created {evidence_id} for hypothesis {body.hypothesis_id}")
    return {**entry, "hypothesis_id": body.hypothesis_id}


@router.put("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    body: EvidenceUpdate,
    hypothesis_id: int = Query(..., description="所属假设ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新指定证据条目"""
    hypo = await _get_hypo_or_404(hypothesis_id, user, db)
    chain = _parse_chain(hypo.evidence_chain)

    target = next((e for e in chain if e.get("id") == evidence_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="证据条目不存在")

    # 安全检查
    if body.content is not None:
        is_safe, reason = prompt_guard.check(body.content)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"安全检测未通过: {reason}")
        target["content"] = body.content
    if body.source is not None:
        target["source"] = body.source
    if body.evidence_type is not None:
        target["evidence_type"] = body.evidence_type
    if body.strength is not None:
        target["strength"] = body.strength
    if body.tags is not None:
        target["tags"] = body.tags

    hypo.evidence_chain = _serialize_chain(chain)
    await db.commit()

    logger.info(f"[Evidence] Updated {evidence_id}")
    return {**target, "hypothesis_id": hypothesis_id}


@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    hypothesis_id: int = Query(..., description="所属假设ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除指定证据条目"""
    hypo = await _get_hypo_or_404(hypothesis_id, user, db)
    chain = _parse_chain(hypo.evidence_chain)

    new_chain = [e for e in chain if e.get("id") != evidence_id]
    if len(new_chain) == len(chain):
        raise HTTPException(status_code=404, detail="证据条目不存在")

    hypo.evidence_chain = _serialize_chain(new_chain)
    await db.commit()

    logger.info(f"[Evidence] Deleted {evidence_id} from hypothesis {hypothesis_id}")
    return {"ok": True, "deleted_id": evidence_id}


@router.get("/stats")
async def evidence_stats(
    hypothesis_id: int = Query(default=0, description="可选：指定假设ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """证据统计：总数、按类型分布、平均强度"""
    if hypothesis_id:
        hypo = await _get_hypo_or_404(hypothesis_id, user, db)
        chain = _parse_chain(hypo.evidence_chain)
    else:
        # 聚合用户所有项目的假设证据
        stmt = select(Hypothesis).join(Project).where(Project.user_id == user.id)
        rows = (await db.execute(stmt)).scalars().all()
        chain = []
        for h in rows:
            chain.extend(_parse_chain(h.evidence_chain))

    total = len(chain)
    by_type: dict[str, int] = {}
    total_strength = 0.0
    for e in chain:
        t = e.get("evidence_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        total_strength += e.get("strength", 0.0)

    return {
        "total": total,
        "by_type": by_type,
        "avg_strength": round(total_strength / total, 3) if total > 0 else 0.0,
    }
