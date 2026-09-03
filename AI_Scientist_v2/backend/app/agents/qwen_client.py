"""智研星枢 - 通义千问API客户端（带完整追踪）"""
import httpx
import logging
from app.config import settings
from app.observability.tracer import Tracer
from app.observability.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


async def call_qwen(system_prompt: str, user_prompt: str, model: str = None,
                    max_tokens: int = None, temperature: float = None,
                    project_id: int = None, task_id: int = None) -> dict:
    model = model or settings.QWEN_MODEL_NAME
    max_tokens = max_tokens or settings.QWEN_MAX_TOKENS
    temperature = temperature if temperature is not None else settings.QWEN_TEMPERATURE

    if not settings.QWEN_API_KEY or settings.QWEN_API_KEY.startswith("sk-xxxx"):
        raise ValueError("QWEN_API_KEY未配置，请在backend/.env中设置有效的通义千问API密钥")

    span = Tracer.create_span("llm_call", f"qwen:{model}", project_id=project_id, task_id=task_id)
    span.set_input({"system": system_prompt[:500], "user": user_prompt[:2000]})
    span.metadata = {"model": model, "max_tokens": max_tokens, "temperature": temperature}

    try:
        async with httpx.AsyncClient(timeout=180.0, headers={"Accept-Encoding": "identity"}) as client:
            resp = await client.post(API_URL, json={
                "model": model, "temperature": temperature, "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }, headers={"Authorization": f"Bearer {settings.QWEN_API_KEY}", "Content-Type": "application/json"})
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        inp_tokens = usage.get("prompt_tokens", cost_tracker.estimate_tokens(system_prompt + user_prompt))
        out_tokens = usage.get("completion_tokens", cost_tracker.estimate_tokens(content))
        cost = cost_tracker.calculate_cost(model, inp_tokens, out_tokens)

        span.set_output({"content": content[:5000], "finish_reason": data["choices"][0].get("finish_reason")})
        span.tokens_used = inp_tokens + out_tokens
        span.cost_yuan = cost
        Tracer.finish_span(span)

        fr=data["choices"][0].get("finish_reason","")
        if fr=="length": logger.warning(f"[QWEN] truncated max={max_tokens} out={out_tokens}")
        return {"content": content, "tokens": {"input": inp_tokens, "output": out_tokens}, "model": model, "cost": cost, "finish_reason": fr}
    except httpx.TimeoutException:
        span.set_error("API调用超时(120s)")
        Tracer.finish_span(span)
        raise TimeoutError("通义千问API调用超时")
    except httpx.HTTPStatusError as e:
        err = f"HTTP {e.response.status_code}: {e.response.content.decode("utf-8")[:300]}"
        span.set_error(err)
        Tracer.finish_span(span)
        raise RuntimeError(f"通义千问API错误: {err}")
    except Exception as e:
        span.set_error(str(e))
        Tracer.finish_span(span)
        raise