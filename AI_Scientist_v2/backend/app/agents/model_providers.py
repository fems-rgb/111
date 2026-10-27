"""智研星枢 - 多模型供应商注册表

背景：所有 LLM 调用都走 qwen_client.call_qwen，过去把 DashScope 端点和
QWEN_API_KEY 写死在客户端里。DeepSeek / Moonshot Kimi / 智谱 GLM 以及任意
"通用 OpenAI 兼容"端点暴露的都是同一套 /chat/completions 接口，因此把
"模型名 → (base_url, api_key, 供应商)" 抽成一张注册表，call_qwen 只需按模型名
查表即可，重试 / 换模型 / trace / cost 管线全部原样复用。

扩展方式：在 backend/.env 里给对应供应商配置 *_API_KEY（密钥留空则该供应商整体
不出现，下拉与生成都不会暴露它）；自定义端点需 Base URL + Key + 模型名三者齐全。
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)


def _split_names(raw: str) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def _key_ok(key: str) -> bool:
    """密钥是否可用：非空且不是样板里的占位值"""
    return bool(key) and not key.startswith("sk-xxxx")


class Provider:
    """一个模型供应商：一个 OpenAI 兼容端点 + 一把密钥 + 若干模型名"""

    def __init__(self, pid: str, label: str, base_url: str, api_key: str, models: list[str],
                 env_key: str = "", hint: str = "", local: bool = False):
        self.id = pid
        self.label = label
        self.base_url = base_url
        self.api_key = api_key
        self.models = models
        self.env_key = env_key or "API Key"
        # hint：领 key / 启用方式的说明（未配 key 时展示给用户，告诉他怎么解锁）
        self.hint = hint
        # local：本地端点（如 Ollama），无需真实密钥、但需本机服务在跑
        self.local = local

    @property
    def configured(self) -> bool:
        return _key_ok(self.api_key)

    def to_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "models": list(self.models),
                "configured": self.configured, "hint": self.hint, "local": self.local}


def build_providers() -> list[Provider]:
    """依据当前 settings（进程启动时读取 .env）构造供应商列表。

    通义千问始终存在（向后兼容：它是默认档与回退链的归宿）；其余供应商仅在
    配置了密钥后才出现，自定义端点还要求 Base URL 与模型名齐全。
    """
    providers = [
        Provider("qwen", "通义千问", settings.QWEN_BASE_URL,
                 settings.QWEN_API_KEY, _split_names(settings.QWEN_FALLBACK_MODELS) +
                 [settings.QWEN_MODEL_NAME, "qwen-turbo", "qwen-plus", "qwen-max",
                  "qwen-max-longcontext"], env_key="QWEN_API_KEY"),
        Provider("deepseek", "DeepSeek", settings.DEEPSEEK_BASE_URL,
                 settings.DEEPSEEK_API_KEY, _split_names(settings.DEEPSEEK_MODELS),
                 env_key="DEEPSEEK_API_KEY"),
        Provider("moonshot", "Moonshot Kimi", settings.MOONSHOT_BASE_URL,
                 settings.MOONSHOT_API_KEY, _split_names(settings.MOONSHOT_MODELS),
                 env_key="MOONSHOT_API_KEY"),
        Provider("zhipu", "智谱 GLM", settings.ZHIPU_BASE_URL,
                 settings.ZHIPU_API_KEY, _split_names(settings.ZHIPU_MODELS),
                 env_key="ZHIPU_API_KEY",
                 hint="open.bigmodel.cn 注册领免费 key（glm-4-flash 免费）"),
        Provider("gemini", "Google Gemini", settings.GEMINI_BASE_URL,
                 settings.GEMINI_API_KEY, _split_names(settings.GEMINI_MODELS),
                 env_key="GEMINI_API_KEY",
                 hint="aistudio.google.com 免费领 key，快且强"),
        Provider("groq", "Groq", settings.GROQ_BASE_URL,
                 settings.GROQ_API_KEY, _split_names(settings.GROQ_MODELS),
                 env_key="GROQ_API_KEY",
                 hint="console.groq.com 免费领 key，推理速度极快"),
        Provider("siliconflow", "硅基流动", settings.SILICONFLOW_BASE_URL,
                 settings.SILICONFLOW_API_KEY, _split_names(settings.SILICONFLOW_MODELS),
                 env_key="SILICONFLOW_API_KEY",
                 hint="cloud.siliconflow.cn 注册送免费额度，中文友好"),
        Provider("openrouter", "OpenRouter", settings.OPENROUTER_BASE_URL,
                 settings.OPENROUTER_API_KEY, _split_names(settings.OPENROUTER_MODELS),
                 env_key="OPENROUTER_API_KEY",
                 hint="openrouter.ai 领 key，:free 后缀模型免费"),
    ]
    # Ollama 本地：无需密钥（默认已占位 key），本机装并运行 Ollama 后即可用
    if settings.OLLAMA_BASE_URL and _split_names(settings.OLLAMA_MODELS):
        providers.append(Provider("ollama", "Ollama 本地（免费离线）", settings.OLLAMA_BASE_URL,
                                  settings.OLLAMA_API_KEY, _split_names(settings.OLLAMA_MODELS),
                                  env_key="OLLAMA_API_KEY", local=True,
                                  hint="本机安装并运行 ollama，再 ollama pull qwen2.5:7b 即可"))
    if settings.CUSTOM_BASE_URL and _split_names(settings.CUSTOM_MODELS):
        providers.append(Provider("custom", "自定义（OpenAI 兼容）", settings.CUSTOM_BASE_URL,
                                  settings.CUSTOM_API_KEY, _split_names(settings.CUSTOM_MODELS),
                                  env_key="CUSTOM_API_KEY"))

    # 去重每个供应商内部的模型名，保序
    for p in providers:
        seen: set[str] = set()
        p.models = [m for m in p.models if not (m in seen or seen.add(m))]
    return providers


_PROVIDERS: list[Provider] = build_providers()
# 统一以 qwen 端点兜底：未注册模型（含历史回退名）仍按通义千问处理，保持旧行为
_INDEX: dict[str, Provider] = {}
for _p in _PROVIDERS:
    for _m in _p.models:
        _INDEX.setdefault(_m, _p)
_DEFAULT_PROVIDER: Provider = _PROVIDERS[0]  # qwen 恒在首位


def providers() -> list[Provider]:
    return _PROVIDERS


def configured_providers() -> list[Provider]:
    """仅返回已配置密钥的供应商（供下拉展示与"是否有任何可用模型"判断）"""
    return [p for p in _PROVIDERS if p.configured]


def provider_for_model(model: str) -> Provider | None:
    return _INDEX.get((model or "").strip())


def endpoint_for_model(model: str) -> tuple[str, str, Provider]:
    """model → (base_url, api_key, provider)。未注册模型回退到通义千问端点。"""
    p = _INDEX.get((model or "").strip()) or _DEFAULT_PROVIDER
    return p.base_url, p.api_key, p


def all_model_names() -> list[str]:
    """全体供应商的模型名（白名单校验用），保序去重"""
    out: list[str] = []
    for p in _PROVIDERS:
        for m in p.models:
            if m not in out:
                out.append(m)
    return out


def is_supported(model: str) -> bool:
    return (model or "").strip() in _INDEX
