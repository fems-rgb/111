"""Document Reviewer Agent - reviews sections and full documents"""
import json, logging
from typing import Optional
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class SectionReviewerAgent(BaseAgent):
    name = "section_reviewer"
    display_name = "🔍 章节审稿Agent"
    description = "审查章节内容质量、逻辑一致性、多模态完整性"
    requires_review = False
    max_retries = 2
    timeout_seconds = 120

    system_prompt = """You are a rigorous academic peer reviewer. Evaluate the section against these criteria:
1. Content completeness: all required elements present?
2. Evidence quality: statistical claims specific (coefficient, p-value, CI, effect size)?
3. Logic consistency: no contradictions with prior sections?
4. Multimodal correctness: Mermaid/LaTeX/tables syntactically valid and renderable?
5. Word count within specified range?
6. No fabricated data or unsupported claims?

Output strict JSON:
{
  "approved": true/false,
  "score": 1-10,
  "issues": [{"type": "category", "severity": "high|medium|low", "description": "...", "suggestion": "..."}],
  "summary": "brief review summary"
}"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        section_id = kwargs.get("section_id", "unknown")
        section_content = kwargs.get("section_content", "")
        section_spec = kwargs.get("section_spec")
        spec_desc = ""
        if section_spec:
            spec_desc = f"Section: {section_spec.section_id} | {section_spec.title_cn}({section_spec.title_en})" + NL
            spec_desc += f"Required elements: {section_spec.required_elements}" + NL
            spec_desc += f"Word range: {section_spec.min_words}-{section_spec.max_words}" + NL
            spec_desc += f"Multimodal hints: {section_spec.multimodal_hints}"
        return f"""## Review Request
{spec_desc}

## Research Question
{research_question}

## Section Content to Review
{section_content}

## Prior Context (summary)
{context[:3000]}

Review strictly per criteria. Output JSON."""

    def parse_review(self, raw_output: str) -> dict:
        try:
            text = raw_output.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"[SectionReviewer] JSON parse failed: {e}")
            return {"approved": False, "score": 0, "issues": [], "error": str(e)}


class DocumentReviewerAgent(BaseAgent):
    name = "document_reviewer"
    display_name = "📝 全文审稿Agent"
    description = "审查完整文档的整体质量、结构完整性、学术规范"
    requires_review = False
    max_retries = 2
    timeout_seconds = 180

    system_prompt = """You are a senior journal editor reviewing a complete academic document. Evaluate:
1. Overall structure coherence and logical flow
2. Cross-section consistency (terminology, hypothesis IDs, variable names)
3. All multimodal elements renderable and properly referenced
4. Citation format compliance
5. Bilingual title compliance (if required)
6. Total word count within target range
7. No orphaned [pending] markers without justification

Output strict JSON:
{
  "approved": true/false,
  "overall_score": 1-10,
  "section_scores": {"section_id": score},
  "critical_issues": ["list of must-fix issues"],
  "suggestions": ["optional improvements"],
  "ready_for_submission": true/false
}"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        document = kwargs.get("document", "")
        template_id = kwargs.get("template_id", "")
        plan = kwargs.get("plan", {})
        return f"""## Full Document Review
Template: {template_id}
Research Question: {research_question}

## Complete Document
{document}

## Generation Plan Summary
{json.dumps(plan, ensure_ascii=False, indent=2)[:2000]}

Review as senior editor. Output JSON."""

    def parse_review(self, raw_output: str) -> dict:
        try:
            text = raw_output.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"[DocumentReviewer] JSON parse failed: {e}")
            return {"approved": False, "overall_score": 0, "error": str(e)}