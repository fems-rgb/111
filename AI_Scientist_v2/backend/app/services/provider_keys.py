"""运行时模型供应商密钥（管理员在模型下拉里直接填写，免改 .env、免重启）

为什么需要：`model_providers` 只在进程启动时按 `settings` 建一次索引，未配 key 的
供应商在界面上只能看到「填 key 即用」的提示，用户无法自助启用。这里把管理员在
界面上填的 key 落到 `backend/.provider_keys.json`（已 gitignore），并在启动与保存后
注入 settings，再重建供应商索引，做到「填完立刻可选」。

优先级：运行时填入 > .env 原值。清除运行时 key 后自动回退到 .env 原值。
安全：文件仅本机可读；接口只返回「是否已配置」，绝不回显 key 明文。
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# backend/.provider_keys.json（与运行 cwd 无关）
STORE = Path(__file__).resolve().parent.parent.parent / ".provider_keys.json"

# provider id → settings 属性名，必须与 model_providers.build_providers 的 env_key 一致
ENV_BY_PROVIDER: dict[str, str] = {
    "qwen": "QWEN_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    "custom": "CUSTOM_API_KEY",
}

# 启动时的 .env 原值快照：清除运行时 key 时用它回退，避免把 .env 里的 key 一起抹掉
_ORIGINALS: dict[str, str] = {attr: getattr(settings, attr, "") for attr in ENV_BY_PROVIDER.values()}


def load() -> dict[str, str]:
    """读取已保存的运行时 key（文件缺失/损坏都当空，不影响启动）"""
    try:
        if not STORE.exists():
            return {}
        data = json.loads(STORE.read_text(encoding="utf-8") or "{}")
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items() if str(v).strip()}
    except Exception as e:
        logger.warning(f"读取运行时密钥失败（忽略）: {e}")
        return {}


def _write(data: dict[str, str]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, STORE)
    try:  # 仅本机可读（Windows 上 chmod 语义有限，尽力而为）
        os.chmod(STORE, 0o600)
    except Exception:
        pass


def save(provider_id: str, api_key: str) -> str:
    """保存某个供应商的密钥；返回去除首尾空白后的密钥"""
    pid = (provider_id or "").strip().lower()
    if pid not in ENV_BY_PROVIDER:
        raise KeyError(pid)
    key = (api_key or "").strip()
    if not key:
        raise ValueError("密钥不能为空")
    data = load()
    data[pid] = key
    _write(data)
    return key


def clear(provider_id: str) -> bool:
    """删除某个供应商的运行时密钥；返回是否确实删掉了"""
    pid = (provider_id or "").strip().lower()
    data = load()
    if pid not in data:
        return False
    data.pop(pid, None)
    _write(data)
    return True


def apply(settings_obj=settings) -> dict[str, str]:
    """把运行时 key 注入 settings：有则覆盖，无则回退到 .env 原值"""
    stored = load()
    for pid, attr in ENV_BY_PROVIDER.items():
        runtime = (stored.get(pid) or "").strip()
        setattr(settings_obj, attr, runtime or _ORIGINALS.get(attr, ""))
    return stored


def has_runtime_key(provider_id: str) -> bool:
    return bool((load().get((provider_id or "").strip().lower()) or "").strip())
