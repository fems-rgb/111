"""模型供应商 API —— 让管理员在「选模型」下拉里直接填 key 启用供应商

设计要点：
- 密钥只写不读：列表接口仅返回「是否已配置」，绝不回显明文；
- 保存/清除后立即重建 model_providers 索引，无需重启后端；
- 仅管理员可改（写的是整台部署的密钥，不是个人偏好）；
- 同时清掉该供应商模型的限流/未开通标记，换 key 后能立即重试。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agents import model_providers, qwen_client
from app.api.deps import require_admin
from app.database.models import User
from app.services import provider_keys

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["模型供应商"])


class ProviderKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=4, max_length=500)


def _provider_out(p: model_providers.Provider) -> dict:
    return {
        "id": p.id, "label": p.label, "env_key": p.env_key, "hint": p.hint,
        "configured": p.configured, "local": p.local,
        "models": list(p.models),
        # 是否来自界面填入（可用于前端提示「可在界面清除」），不暴露任何密钥片段
        "runtime": provider_keys.has_runtime_key(p.id),
    }


@router.get("")
async def list_providers(user: User = Depends(require_admin)):
    """当前部署的供应商与启用状态（不含任何密钥明文）"""
    provs = model_providers.providers()
    return {"items": [_provider_out(p) for p in provs],
            "configured": sum(1 for p in provs if p.configured), "total": len(provs)}


@router.post("/{provider_id}/key")
async def save_provider_key(provider_id: str, req: ProviderKeyRequest,
                            user: User = Depends(require_admin)):
    """保存供应商密钥并立即生效（返回本次新解锁的模型名）"""
    pid = (provider_id or "").strip().lower()
    if pid not in provider_keys.ENV_BY_PROVIDER:
        raise HTTPException(status_code=400,
                            detail=f"该供应商不支持在界面填 key：{provider_id}（请改用 .env 配置）")
    key = (req.api_key or "").strip()
    if len(key) < 4:
        raise HTTPException(status_code=400, detail="API Key 太短，请检查是否粘贴完整")

    before = {m for p in model_providers.providers() if p.id == pid for m in p.models}
    try:
        provider_keys.save(pid, key)
    except Exception as e:
        logger.exception("保存供应商密钥失败")
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)[:120]}")

    provs = model_providers.reload()
    p = next((x for x in provs if x.id == pid), None)
    if not p:
        raise HTTPException(status_code=500, detail="密钥已保存，但供应商重建失败，请重启后端")
    if not p.configured:
        raise HTTPException(status_code=400,
                            detail="密钥格式不被接受（请勿填 sk-xxxx 这类占位值）")

    # 换 key 后清除该供应商的历史限流标记，避免刚配好就显示「暂限流」
    qwen_client.clear_block(p.models)
    unlocked = [m for m in p.models if m not in before]
    logger.info(f"🔑 管理员 {user.id} 更新供应商 {pid} 密钥，供应商已配置={p.configured}")
    return {"ok": True, "provider": _provider_out(p), "unlocked": unlocked,
            "configured": sum(1 for x in provs if x.configured), "total": len(provs)}


@router.delete("/{provider_id}/key")
async def clear_provider_key(provider_id: str, user: User = Depends(require_admin)):
    """清除界面填入的密钥，回退到 .env 原值"""
    pid = (provider_id or "").strip().lower()
    if pid not in provider_keys.ENV_BY_PROVIDER:
        raise HTTPException(status_code=400, detail=f"未知模型供应商：{provider_id}")
    removed = provider_keys.clear(pid)
    provs = model_providers.reload()
    p = next((x for x in provs if x.id == pid), None)
    return {"ok": True, "removed": removed,
            "provider": _provider_out(p) if p else None,
            "configured": sum(1 for x in provs if x.configured), "total": len(provs)}
