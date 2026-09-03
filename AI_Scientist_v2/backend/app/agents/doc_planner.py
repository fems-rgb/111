"""Doc Planner + Section Writer Agents"""
import json, logging
from typing import Optional
from app.agents.base import BaseAgent
from app.contracts.document_template import DocumentTemplate, SectionSpec, SectionType, TEMPLATE_REGISTRY, get_template

logger = logging.getLogger(__name__)

NL = "\n"


class DocumentPlannerAgent(BaseAgent):
    name = "document_planner"
    display_name = "📋 文档规划Agent"
    description = "根据研究问题动态规划文档结构"
    requires_review = False
    max_retries = 2
    timeout_seconds = 120

    system_prompt = """You are a senior academic document architect. Analyze the research question and prior results, then plan document structure based on the given template. Output strict JSON only.

JSON Schema:
{{
  "template_id": "template ID used",
  "estimated_total_words": 8000,
  "section_plans": [
    {{
      "section_id": "section ID",
      "content_outline": ["key points list"],
      "key_evidence": ["key evidence to cite"],
      "multimodal_plan": [
        {{"type": "mermaid|latex|table|chart", "description": "detail", "data_source": "source"}}
      ],
      "estimated_words": 800,
      "dependencies_met": true,
      "writing_priority": 1
    }}
  ],
  "cross_section_notes": "cross-section notes",
  "hypothesis_list": ["H1: ...", "H2: ..."],
  "variable_mapping": {{"independent": [], "dependent": [], "control": []}}
}}"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        template_id = kwargs.get("template_id", "nh_202619_track1")
        template = get_template(template_id)
        sections_desc = NL.join([
            f"- {i+1}. {s.section_id}: {s.title_cn}({s.title_en}) [{s.min_words}-{s.max_words}chars] "
            f"type:{s.section_type.value} multimodal:{chr(44).join(s.multimodal_hints)}"
            for i, s in enumerate(template.sections)])
        rules = NL.join(f"- {r}" for r in template.global_quality_rules)
        return f"""## Research Question
{research_question}

## Prior Results Summary
{context[:6000]}

## Template: {template.template_id} - {template.template_name}
Word count: {template.total_min_words}-{template.total_max_words}
Citation: {template.citation_style}, Bilingual: {template.requires_bilingual}

### Sections:
{sections_desc}

### Global Rules:
{rules}

## Task
Plan the document. Keep hypothesis IDs (H1,H2...) consistent. Unify variable names. Identify multimodal needs. Mark dependencies and writing priority. Base plans on actual prior results, never fabricate.

Output JSON."""

    def parse_plan(self, raw_output: str) -> dict:
        try:
            text = raw_output.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.warning(f"[DocumentPlanner] JSON parse failed: {e}")
            return {"section_plans": [], "error": str(e)}


class SectionWriterAgent(BaseAgent):
    name = "section_writer"
    display_name = "✍️ 章节写作Agent"
    description = "按章节规格生成高质量学术内容"
    requires_review = False
    max_retries = 3
    timeout_seconds = 180

    system_prompt = """You are a top academic writing expert. Principles:
1. Every paragraph must have substance, no filler
2. Statistical claims must be specific: coefficient direction, significance level, effect size, CI
3. Distinguish evidence: empirical / theoretical / inference / pending
4. Mark [pending] when info insufficient, never fabricate
5. Multimodal elements must be complete and renderable:
   - Mermaid: full syntax in ```mermaid blocks
   - LaTeX formulas: use $...$ (inline) or $$...$$ (display)
   - Tables: standard Markdown table syntax
6. Rigorous logic: every claim backed by evidence
7. Academic but clear style"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        section_spec: Optional[SectionSpec] = kwargs.get("section_spec")
        section_plan: dict = kwargs.get("section_plan", {})
        completed_sections: dict = kwargs.get("completed_sections", {})
        hypothesis_list: list = kwargs.get("hypothesis_list", [])
        if not section_spec:
            raise ValueError("SectionWriterAgent requires section_spec")
        ctx_parts = [f"[{sid}summary]: {c[:500]}" for sid, c in completed_sections.items()]
        prior = NL.join(ctx_parts)[:4000]
        mm_req = ""
        if section_spec.multimodal_hints:
            items = []
            for h in section_spec.multimodal_hints:
                if "mermaid" in h:
                    items.append(f"- Include complete Mermaid diagram (type: {h}) in ```mermaid block")
                elif "latex" in h or "formula" in h:
                    items.append(f"- Include LaTeX formulas using $...$ inline or $$...$$ display")
                elif "table" in h:
                    items.append("- Include standard Markdown data table")
                elif "chart" in h:
                    items.append("- Include visualization chart or Mermaid diagram")
            mm_req = NL.join(items)
        hypo = ""
        if hypothesis_list:
            hypo = NL + "Hypothesis IDs (must be consistent):" + NL + NL.join(f"  {x}" for x in hypothesis_list)
        outline = ""
        if section_plan.get("content_outline"):
            outline = NL + "Planned outline:" + NL + NL.join(f"  - {p}" for p in section_plan["content_outline"])
        elems = NL.join(f"- {e}" for e in section_spec.required_elements)
        return f"""## Section Spec
ID: {section_spec.section_id}
Title: ## {section_spec.title_cn}({section_spec.title_en})
Words: {section_spec.min_words}-{section_spec.max_words}
Type: {section_spec.section_type.value}

## Required Elements
{elems}

## Writing Guide
{section_spec.template_instructions}

## Multimodal Requirements
{mm_req if mm_req else "No special multimodal requirements; tables encouraged"}

## Research Question
{research_question}
{hypo}
{outline}

## Prior Sections Summary
{prior if prior else "(first section)"}

## Prior Results
{context[:5000]}

## Output Rules
1. Start with "## {section_spec.title_cn}({section_spec.title_en})"
2. Output section content directly, no meta-commentary
3. Word count: {section_spec.min_words}-{section_spec.max_words}
4. Mark [pending] if info insufficient
5. All statistical claims need evidence
6. Consistent terminology with prior sections"""