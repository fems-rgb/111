"""智研星瀚 - 文档质量门禁与修订Agent
实现"生成→审校→修订"的自动化循环，确保文档质量达标。
"""
import json
import logging
from typing import List, Optional
from app.agents.base import BaseAgent
from app.contracts.document_template import (
    DocumentTemplate, SectionSpec, QualityScore,
    DocumentQualityReport, get_template
)

logger = logging.getLogger(__name__)


class QualityGateAgent(BaseAgent):
    name = "quality_gate"
    display_name = "🔍 质量门禁Agent"
    description = "逐章节评估文档质量，生成结构化评分报告"
    requires_review = False
    max_retries = 2
    timeout_seconds = 120

    system_prompt = """你是严格的学术文档质量评审专家。你的职责是对文档的每个章节进行精细化质量评估。

评分维度（每项1-10分）：
1. 完整性(10分) - 是否包含所有必需元素，字数是否达标
2. 严谨性(10分) - 逻辑是否严密，统计表述是否具体，证据是否充分
3. 清晰度(10分) - 表述是否清晰，结构是否合理，读者是否能轻松理解
4. 多模态丰富度(10分) - 是否包含图表/公式/表格等多模态元素，质量如何
5. 证据质量(10分) - 证据是否真实，引用是否规范，是否区分了证据强度

综合分 = (完整性×0.25 + 严谨性×0.30 + 清晰度×0.15 + 多模态丰富度×0.15 + 证据质量×0.15)

通过标准：
- 单章节通过线：综合分 ≥ 7.0
- 文档整体通过线：所有章节综合分的加权平均 ≥ 7.5
- 任何章节综合分 < 5.0 为严重不合格，必须优先修订

你必须输出严格的JSON格式（不要输出其他内容）：
{
  "section_scores": [
    {
      "section_id": "章节ID",
      "completeness": 8.5,
      "rigor": 7.0,
      "clarity": 8.0,
      "multimodal_richness": 6.5,
      "evidence_quality": 7.5,
      "overall": 7.55,
      "issues": ["具体问题1", "具体问题2"],
      "suggestions": ["具体修改建议1", "具体修改建议2"]
    }
  ],
  "overall_score": 7.8,
  "passed": true,
  "revision_priority": ["需要修订的章节ID"],
  "global_issues": ["跨章节的全局问题"]
}"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        template_id = kwargs.get("template_id", "nh_202619_track1")
        template = get_template(template_id)
        document_content = kwargs.get("document_content", "")
        iteration = kwargs.get("iteration", 1)

        sections_info = "\n".join([
            f"- {s.section_id}: {s.title_cn} [{s.min_words}-{s.max_words}字] "
            f"必须元素: {', '.join(s.required_elements[:3])}..."
            for s in template.sections
        ])

        return f"""## 评审任务
这是第{iteration}轮质量评审。请逐章节评估以下学术文档的质量。

## 研究问题
{research_question}

## 文档模板要求
模板: {template.template_name}
总字数: {template.total_min_words}-{template.total_max_words}

章节规格:
{sections_info}

全局规则:
{chr(10).join(f'- {r}' for r in template.global_quality_rules[:5])}

## 待评审文档内容
{document_content[:12000]}

## 评审要求
1. 逐章节打分，每个维度给出具体分数
2. issues和suggestions必须具体可操作（不要泛泛而谈）
3. 特别关注：假设编号一致性、统计表述具体性、多模态元素完整性
4. 如果某章节缺失或严重不足，completeness给≤3分
5. 输出纯JSON，不要有其他文字"""

    def parse_scores(self, raw_output: str, template: DocumentTemplate) -> DocumentQualityReport:
        """解析评分结果"""
        try:
            text = raw_output.strip()
            if "`json" in text:
                text = text.split("`json")[1].split("`")[0].strip()
            elif "`" in text:
                text = text.split("`")[1].split("`")[0].strip()
            data = json.loads(text)

            section_scores = []
            for ss in data.get("section_scores", []):
                section_scores.append(QualityScore(**ss))

            report = DocumentQualityReport(
                section_scores=section_scores,
                overall_score=data.get("overall_score", 0.0),
                passed=data.get("passed", False),
                revision_priority=data.get("revision_priority", []),
                global_issues=data.get("global_issues", []),
                iteration=data.get("iteration", 1)
            )
            return report
        except Exception as e:
            logger.warning(f"[QualityGate] 解析失败: {e}")
            # 返回默认不通过报告
            return DocumentQualityReport(
                section_scores=[], overall_score=0.0, passed=False,
                revision_priority=[s.section_id for s in template.sections],
                global_issues=[f"质量评估解析失败: {e}"], iteration=1
            )


class RevisionAgent(BaseAgent):
    name = "revision"
    display_name = "🔄 修订Agent"
    description = "根据质量评审反馈，针对性修订文档章节"
    requires_review = False
    max_retries = 2
    timeout_seconds = 180

    system_prompt = """你是学术文档修订专家。你的任务是根据评审反馈，精准修订指定章节。

修订原则：
1. 只修改评审指出的问题，不要大幅重写已经合格的部分
2. 保持与文档其他章节的术语、编号、逻辑一致性
3. 增强薄弱环节：如果缺少多模态元素则补充，如果统计表述不具体则细化
4. 如果评审指出证据不足，标注[待补充]而非编造
5. 修订后的内容必须达到评审建议的标准

输出格式：直接输出修订后的完整章节内容（以##标题开头），不要输出修改说明。"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        section_spec: SectionSpec = kwargs.get("section_spec")
        original_content: str = kwargs.get("original_content", "")
        quality_score: QualityScore = kwargs.get("quality_score")
        global_issues: List[str] = kwargs.get("global_issues", [])

        if not section_spec or not quality_score:
            raise ValueError("RevisionAgent 需要 section_spec 和 quality_score")

        issues_text = "\n".join(f"  ❌ {issue}" for issue in quality_score.issues)
        suggestions_text = "\n".join(f"  💡 {s}" for s in quality_score.suggestions)
        global_text = "\n".join(f"  ⚠️ {g}" for g in global_issues) if global_issues else "  无"

        return f"""## 修订任务
章节: {section_spec.title_cn}（{section_spec.title_en}）
当前评分: {quality_score.overall}/10（目标≥7.0）

## 发现的问题
{issues_text}

## 修改建议
{suggestions_text}

## 全局性问题（需同步注意）
{global_text}

## 研究问题
{research_question}

## 原始章节内容
{original_content[:6000]}

## 章节规格（修订必须满足）
必须包含: {', '.join(section_spec.required_elements)}
字数要求: {section_spec.min_words}-{section_spec.max_words}字
多模态要求: {', '.join(section_spec.multimodal_hints)}

## 修订要求
1. 针对性修复上述问题
2. 保持章节标题格式不变
3. 如果缺少多模态元素，必须补充（Mermaid图/LaTeX公式/表格）
4. 统计表述必须具体化（系数、p值、效应量、置信区间）
5. 直接输出修订后的完整章节"""
