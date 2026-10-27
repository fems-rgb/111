"""智研星枢 - 通义千问API客户端（带完整追踪 + 限流重试 + 模型回退）

为什么需要回退：
- DashScope 的 429(limit_requests) 既可能是「分钟级 RPM 打满」（等几秒就好），
  也可能是「某个模型在本文账号下没有可用配额」（等多久都没用，例如 qwen-turbo）。
- 课件生成是逐章串行调用，中途任意一章 429 直接抛异常，整个作业失败、前面的章节全白做。
所以这里把「重试」和「换模型」放在统一入口里做，任何调用方（课件/对话/Agent）都自动受益。
"""
import asyncio
import logging
import random
import time

import httpx

from app.config import settings
from app.agents import model_providers
from app.observability.tracer import Tracer
from app.observability.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)

# 模型级冷却：{model: (解除时间戳, 原因)}
# 429 冷却 60s（瞬时打满几分钟内会恢复）；403/未开通冷却 15min（换多久都一样）
_MODEL_BLOCK: dict[str, tuple[float, str]] = {}

# 命中这些错误码说明「这个模型本身用不了」，换模型才有意义，重试没意义
_FATAL_MODEL_CODES = {
    "access_denied", "model_not_found", "model_not_supported",
    "invalid_model", "unsupported_model",
}

# 冷却时间（秒）
_TTL_RATE_LIMIT = 60
_TTL_NO_ACCESS = 900


class QwenError(RuntimeError):
    """通义千问调用失败（消息已是可直接展示给用户的中文）"""


class QwenAuthError(QwenError):
    """API Key 无效 / 未配置"""


class QwenRateLimited(QwenError):
    """所有候选模型都因限流或未开通而不可用"""


def model_status() -> dict[str, dict]:
    """给前端模型下拉用的可用性快照（进程内记忆，重启即清空）"""
    now = time.time()
    return {
        m: {"blocked_seconds": max(0, int(until - now)), "reason": reason}
        for m, (until, reason) in _MODEL_BLOCK.items() if until > now
    }


def _mark_block(model: str, seconds: int, reason: str) -> None:
    _MODEL_BLOCK[model] = (time.time() + seconds, reason)


def _error_info(payload) -> tuple[str, str]:
    """从 DashScope 错误体里取 (code, message)，兼容两种包裹层级"""
    if not isinstance(payload, dict):
        return "", str(payload)[:300]
    err = payload.get("error")
    if isinstance(err, dict):
        return str(err.get("code") or ""), str(err.get("message") or "")
    return str(payload.get("code") or ""), str(payload.get("message") or str(payload)[:300])


def _fallback_chain(preferred: str) -> list[str]:
    """首选模型 + 本供应商同类回退 + 配置的回退链（去重保序）

    跨供应商选择时不硬拼其他家的模型：若首选模型属于非通义供应商，
    仅在该供应商内部回退；同供应商没有余下候选时再回退到通义系（兼容旧行为）。
    """
    chain = [preferred]
    pref_provider = model_providers.provider_for_model(preferred)
    if pref_provider and pref_provider.id != "qwen":
        for m in pref_provider.models:
            if m != preferred and m not in chain:
                chain.append(m)
    for m in (settings.QWEN_FALLBACK_MODELS or "").split(","):
        m = m.strip()
        if m and m not in chain:
            chain.append(m)
    default = (settings.QWEN_MODEL_NAME or "").strip()
    if default and default not in chain:
        chain.append(default)
    return chain


def _usable_models(preferred: str) -> list[str]:
    """过滤掉冷却中的模型；全部冷却时挑最快解除的那个试一次

    全冷却还硬等没意义（用户会以为卡死），剩余时间过久就直接抛出可读错误。
    """
    chain = _fallback_chain(preferred)
    now = time.time()
    alive = [m for m in chain if _MODEL_BLOCK.get(m, (0, ""))[0] <= now]
    if alive:
        return alive
    soonest = min(chain, key=lambda m: _MODEL_BLOCK.get(m, (0, ""))[0])
    wait = int(_MODEL_BLOCK.get(soonest, (0, ""))[0] - now)
    if wait > 20:
        detail = "；".join(
            f"{m} 还需 {max(0, int(_MODEL_BLOCK.get(m, (0, ''))[0] - now))}s"
            for m in chain
        )
        raise QwenRateLimited(
            f"候选模型暂时不可用（请求额度受限）。{detail}。"
            "可以稍后再试，或到对应供应商控制台确认模型配额。"
        )
    return [soonest]


async def _post_chat(model: str, payload: dict, base_url: str, api_key: str) -> tuple[int, dict | str, dict]:
    async with httpx.AsyncClient(timeout=180.0, headers={"Accept-Encoding": "identity"}) as client:
        resp = await client.post(
            base_url,
            json={"model": model, **payload},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    return resp.status_code, data, dict(resp.headers)


async def call_qwen(system_prompt: str, user_prompt: str, model: str = None,
                    max_tokens: int = None, temperature: float = None,
                    project_id: int = None, task_id: int = None) -> dict:
    """调用通义千问；429/5xx 自动重试，模型不可用自动换下一个

    返回值里的 model 是「实际使用」的模型，fallback_from 记录原首选模型（未回退则为 None）。
    """
    preferred = model or settings.QWEN_MODEL_NAME
    max_tokens = max_tokens or settings.QWEN_MAX_TOKENS
    temperature = temperature if temperature is not None else settings.QWEN_TEMPERATURE

    if not model_providers.configured_providers():
        raise QwenAuthError(
            "未配置任何模型供应商密钥，请在 backend/.env 设置 QWEN_API_KEY"
            "（或 DEEPSEEK_API_KEY / MOONSHOT_API_KEY / ZHIPU_API_KEY / CUSTOM_API_KEY）"
        )

    chain = _usable_models(preferred)
    attempts = max(1, int(settings.QWEN_MAX_RETRIES or 1))
    payload = {
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    span = Tracer.create_span("llm_call", f"llm:{preferred}", project_id=project_id, task_id=task_id)
    span.set_input({"system": system_prompt[:500], "user": user_prompt[:2000]})
    span.metadata = {"model": preferred, "max_tokens": max_tokens, "temperature": temperature}

    tried: list[str] = []
    last_error = ""

    for m in chain:
        tried.append(m)
        base_url, api_key, provider = model_providers.endpoint_for_model(m)
        if not api_key or api_key.startswith("sk-xxxx"):
            # 该供应商未配密钥：标冷却（本进程内不再重试），换下一个候选模型
            _mark_block(m, _TTL_NO_ACCESS, f"{provider.label} 未配置 API Key")
            logger.warning(f"[LLM] {m} 属于 {provider.label}，但未配置密钥，换下一个模型")
            continue
        for i in range(attempts):
            if i > 0:
                # 指数退避 + 抖动：避免多个作业同一秒集体重试再次撞墙
                delay = 1.5 * (2 ** (i - 1)) + random.uniform(0, 0.6)
                logger.warning(f"[LLM] {m} 第 {i} 次失败，{delay:.1f}s 后重试：{last_error[:160]}")
                await asyncio.sleep(delay)
            try:
                status, data, headers = await _post_chat(m, payload, base_url, api_key)
            except asyncio.CancelledError:
                raise
            except httpx.TimeoutException:
                last_error = "请求超时(180s)"
                continue
            except Exception as e:  # 网络抖动
                last_error = f"{type(e).__name__}: {e}"
                continue

            if status == 200 and isinstance(data, dict):
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                inp_tokens = usage.get("prompt_tokens", cost_tracker.estimate_tokens(system_prompt + user_prompt))
                out_tokens = usage.get("completion_tokens", cost_tracker.estimate_tokens(content))
                cost = cost_tracker.calculate_cost(m, inp_tokens, out_tokens)
                finish_reason = data["choices"][0].get("finish_reason", "")

                span.set_output({"content": content[:5000], "finish_reason": finish_reason})
                span.metadata["model"] = m
                span.metadata["fallback_from"] = preferred if m != preferred else None
                span.tokens_used = inp_tokens + out_tokens
                span.cost_yuan = cost
                Tracer.finish_span(span)

                if finish_reason == "length":
                    logger.warning(f"[LLM] truncated model={m} max={max_tokens} out={out_tokens}")
                if m != preferred:
                    logger.warning(f"[LLM] 首选模型 {preferred} 不可用，已自动回退到 {m}")
                return {
                    "content": content,
                    "tokens": {"input": inp_tokens, "output": out_tokens},
                    "model": m,
                    "fallback_from": preferred if m != preferred else None,
                    "cost": cost,
                    "finish_reason": finish_reason,
                }

            code, msg = _error_info(data)
            last_error = f"HTTP {status}: {code or ''} {msg}".strip()[:300]

            if status == 401 or code in {"invalid_api_key", "authentication_error"}:
                span.set_error(last_error)
                Tracer.finish_span(span)
                raise QwenAuthError(
                    f"{provider.label} API Key 无效或已过期，请在 backend/.env 更新 {provider.env_key}"
                )

            if status == 429 or code in {"limit_requests", "throttling", "rate_limit_exceeded"}:
                # 额度/每秒请求数打满：先在本模型上重试，用尽后冷却并换模型
                if i < attempts - 1:
                    continue
                _mark_block(m, _TTL_RATE_LIMIT, "请求额度受限")
                logger.warning(f"[LLM] {m} 限流，冷却 {_TTL_RATE_LIMIT}s 后切换下一个模型")
                break

            if status in (403, 404) or code in _FATAL_MODEL_CODES:
                _mark_block(m, _TTL_NO_ACCESS, "该模型未开通或无权限")
                logger.warning(f"[LLM] {m} 不可用（{code or status}），换模型")
                break

            if status >= 500:
                if i < attempts - 1:
                    continue
                break

            # 400 之类：参数/上下文问题，换模型也大概率不行，直接抛出
            span.set_error(last_error)
            Tracer.finish_span(span)
            raise QwenError(f"{provider.label} API 错误: {last_error}")

    span.set_error(f"全部模型失败: {last_error}")
    span.metadata["tried_models"] = tried
    Tracer.finish_span(span)
    raise QwenRateLimited(
        f"模型请求失败：已尝试 {' / '.join(tried)}，最后一个错误是 {last_error[:160]}。"
        "常见原因：该模型的请求额度已用尽、未开通或密钥未配置；"
        "可在「生成模型」里换一个可用模型，或到对应供应商控制台确认配额与密钥。"
    )
