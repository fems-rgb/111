"""智研星枢 - 智能任务路由器"""
from app.utils.safe_json import safe_json_parse
import json
import logging
from app.agents.qwen_client import call_qwen
from app.database.models import Complexity

logger = logging.getLogger(__name__)

ROUTER_SYSTEM = """你是智研星枢的任务分类器。根据研究问题判断复杂度。
分类：
- simple: 概念解释、简单问答
- workflow: 需要多步骤完整研究流程
- multi_agent: 跨学科复杂问题
只返回JSON：{"complexity":"simple|workflow|multi_agent","reason":"原因","suggested_agents":["agent1"],"suggested_model":"qwen-max|qwen-max|qwen-max"}
可用Agent: literature,design,analysis,writing,review"""


async def route_task(research_question: str, model: str = "qwen-max") -> dict:
    try:
        result = await call_qwen(ROUTER_SYSTEM, research_question, model=model, max_tokens=300, temperature=0.1)
        content = result["content"].strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = safe_json_parse(content,fallback={},label="task_router")
        complexity_map = {"simple": Complexity.SIMPLE, "workflow": Complexity.WORKFLOW, "multi_agent": Complexity.MULTI_AGENT}
        return {
            "complexity": complexity_map.get(parsed.get("complexity", "workflow"), Complexity.WORKFLOW),
            "reason": parsed.get("reason", ""),
            "suggested_agents": parsed.get("suggested_agents", ["literature", "design", "analysis"]),
            "suggested_model": parsed.get("suggested_model", "qwen-max"),
            "tokens": result["tokens"]["input"] + result["tokens"]["output"],
            "cost": result["cost"]
        }
    except Exception as e:
        logger.warning(f"路由判断失败，使用默认workflow: {e}")
        return {
            "complexity": Complexity.WORKFLOW, "reason": f"路由异常，使用默认工作流",
            "suggested_agents": ["literature", "design", "analysis", "writing", "review"],
            "suggested_model": "qwen-max", "tokens": 0, "cost": 0.0
        }