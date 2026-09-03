"""智研星枢 - 科学假设结构化提取与验证"""
from app.utils.safe_json import safe_json_parse
import json
import logging
from typing import Dict, Any
from app.agents.qwen_client import call_qwen

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """你是科研方法论专家与科学哲学研究者。请从以下研究设计文本中提取所有科学假设，并进行5维结构化评估。

严格要求：
1. 每个假设必须是可证伪的具体命题（falsifiable），而非泛泛建议或研究目标
2. 如果某条陈述不可证伪，标记为 invalid 并说明原因
3. 保留反对证据（counter-evidence），即使它削弱假设

严格JSON数组返回，每个假设包含：
- id: 假设编号（H1, H2...）
- statement: 假设陈述（简洁明确，可证伪命题）
- variables: 涉及的变量列表
- testability_score: 可验证性评分（1-10，10=完全可实证检验）
- falsifiability_score: 可证伪性评分（1-10，10=存在明确的反驳条件）
- evidence_consistency: 证据一致性评分（1-10，10=与现有文献完全一致）
- novelty_score: 新颖性评分（1-10，10=完全原创且非显而易见）
- diversity_score: 多样性评分（1-10，与其他候选假设的差异度）
- suggested_method: 建议的验证方法
- evidence_chain: 支撑该假设的文献/理论依据摘要
- counter_evidence: 反对该假设的证据或论点（如无则填"暂无"）
- is_valid: 是否为有效可证伪假设（true/false）
- invalid_reason: 若is_valid=false，说明不可证伪的原因

仅返回JSON数组，不要其他内容。"""

async def extract_and_validate_hypothesis(raw_output: str, research_question: str, model: str = "qwen-max") -> Dict[str, Any]:
    try:
        user_msg = f"研究问题：{research_question}\n\n研究设计文本：\n{raw_output[:6000]}"
        result = await call_qwen(EXTRACT_PROMPT, user_msg, model=model)
        
        # 提取JSON数组
        content = result["content"]
        start = content.find("[")
        end = content.rfind("]") + 1
        hypotheses = []
        if start >= 0 and end > start:
            hypotheses = safe_json_parse(content[start:end],fallback=[],label="hypothesis_validator")
        
        # 生成证据链摘要
        evidence_summary = "\n".join([
            f"{h.get('id','?')}: {h.get('statement','')} [可验证性:{h.get('testability_score',0)}/10]"
            for h in hypotheses
        ])
        
        return {
            "structured_output": json.dumps(hypotheses, ensure_ascii=False, indent=2),
            "evidence_chain": evidence_summary,
            "hypothesis_count": len(hypotheses),
            "avg_testability": sum(h.get("testability_score", 0) for h in hypotheses) / max(len(hypotheses), 1),
            "tokens": result.get("tokens", 0)
        }
    except Exception as e:
        logger.error(f"假设提取失败: {e}", exc_info=True)
        return {
            "structured_output": raw_output,
            "evidence_chain": "[假设提取失败，保留原始输出]",
            "hypothesis_count": 0,
            "avg_testability": 0,
            "tokens": 0
        }

async def get_project_hypotheses(db, project_id: int) -> list[dict]:
    from sqlalchemy import select
    from app.database.models import Hypothesis
    rows = (await db.execute(
        select(Hypothesis)
        .where(Hypothesis.project_id == project_id)
        .order_by(Hypothesis.hypo_id, Hypothesis.version)
    )).scalars().all()
    return [{
        "id": r.id, "hypo_id": r.hypo_id, "statement": r.statement,
        "variables": r.variables or [], "testability_score": r.testability_score,
        "suggested_method": r.suggested_method, "evidence_chain": r.evidence_chain,
        "version": r.version, "parent_id": r.parent_id, "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "novelty_score": r.novelty_score,
        "feasibility_score": r.feasibility_score,
        "impact_score": r.impact_score,
        "overall_score": r.overall_score,
        "ai_reasoning": r.ai_reasoning,
        "literature_refs": r.literature_refs or [],
        "rejected_reason": r.rejected_reason,
    } for r in rows]


