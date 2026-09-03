"""智研星枢 - API调用成本追踪"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

MODEL_PRICING = {
    "qwen-max": {"input": 0.0003, "output": 0.0006},
    "qwen-max": {"input": 0.0008, "output": 0.002},
    "qwen-max": {"input": 0.002, "output": 0.006},
    "qwen-long": {"input": 0.0005, "output": 0.002},
    "qwen-vl-max": {"input": 0.002, "output": 0.005},
    "qwen-vl-max": {"input": 0.003, "output": 0.009},
}


class CostTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.total_tokens = 0
        self.call_count = 0
        self.model_costs = {}

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("qwen-max", {}))
        cost = (input_tokens * pricing.get("input", 0.001) + output_tokens * pricing.get("output", 0.002)) / 1000
        self.total_cost += cost
        self.total_tokens += input_tokens + output_tokens
        self.call_count += 1
        if model not in self.model_costs:
            self.model_costs[model] = {"cost": 0.0, "tokens": 0, "calls": 0}
        self.model_costs[model]["cost"] += cost
        self.model_costs[model]["tokens"] += input_tokens + output_tokens
        self.model_costs[model]["calls"] += 1
        if self.total_cost >= settings.COST_ALERT_THRESHOLD_YUAN:
            logger.warning(f"⚠️ 成本预警: 累计 ¥{self.total_cost:.4f}")
        return cost

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return int(cn / 1.5 + (len(text) - cn) / 4)

    def suggest_model(self, complexity: str) -> str:
        return {"simple": "qwen-max", "workflow": "qwen-max", "multi_agent": "qwen-max"}.get(complexity, "qwen-max")

    def get_summary(self) -> dict:
        return {
            "total_cost_yuan": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
            "avg_cost_per_call": round(self.total_cost / max(self.call_count, 1), 4),
            "model_breakdown": {m: {"cost": round(d["cost"], 4), "tokens": d["tokens"], "calls": d["calls"]} for m, d in self.model_costs.items()}
        }


cost_tracker = CostTracker()