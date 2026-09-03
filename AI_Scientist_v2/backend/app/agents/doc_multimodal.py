"""智研星瀚 - 多模态内容增强Agent
为文档自动生成/优化多模态元素：Mermaid流程图、LaTeX公式、数据表格、图表。
"""
import logging
from typing import List, Dict
from app.agents.base import BaseAgent
from app.contracts.document_template import SectionSpec

logger = logging.getLogger(__name__)


class MultimodalEnricherAgent(BaseAgent):
    name = "multimodal_enricher"
    display_name = "🎨 多模态增强Agent"
    description = "为文档章节生成/增强多模态元素（图表、公式、可视化）"
    requires_review = False
    max_retries = 2
    timeout_seconds = 120

    system_prompt = """你是学术可视化与多模态内容专家。你的任务是为学术文档生成高质量的多模态元素。

能力范围：
1. Mermaid图（流程图、概念图、序列图、甘特图、状态图）
2. LaTeX数学公式（计量模型、统计公式、优化目标）
3. 结构化数据表格（对比矩阵、参数表、结果表）
4. 图表描述与数据可视化方案

输出规范：
- Mermaid: 使用`mermaid代码块，确保语法正确可渲染
- LaTeX: 使用 $$ ... $$ （独立公式）或 $ ... $ （行内公式）
- 表格: 标准Markdown | col | 语法，含表头和分隔行
- 每个多模态元素必须有标题和简要说明文字

质量标准：
- 流程图必须逻辑完整，节点命名清晰
- 公式必须数学正确，变量有明确定义
- 表格必须有实际数据或合理的占位标注[待填充]
- 不编造具体数值，用[待填充]或[基于实际数据]标注"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        section_spec: SectionSpec = kwargs.get("section_spec")
        section_content: str = kwargs.get("section_content", "")
        multimodal_plan: List[dict] = kwargs.get("multimodal_plan", [])
        hypothesis_list: List[str] = kwargs.get("hypothesis_list", [])

        if not section_spec:
            raise ValueError("MultimodalEnricherAgent 需要 section_spec")

        # 构建多模态需求描述
        mm_requirements = []
        for hint in section_spec.multimodal_hints:
            if "mermaid" in hint:
                mm_requirements.append(f"- 生成一个Mermaid图（类型参考: {hint}），展示该章节核心逻辑/流程")
            elif "latex" in hint or "formula" in hint:
                mm_requirements.append(f"- 生成关键公式的LaTeX表达，包含变量定义")
            elif "table" in hint:
                mm_requirements.append(f"- 生成结构化数据表格，包含关键变量/参数/结果")
            elif "chart" in hint:
                mm_requirements.append(f"- 生成数据可视化方案（Mermaid图或表格形式）")
            elif "evidence" in hint:
                mm_requirements.append(f"- 生成证据强度评估表格（✅/📐/⚠️标注）")

        # 来自规划的多模态计划
        plan_text = ""
        if multimodal_plan:
            plan_items = []
            for mp in multimodal_plan:
                plan_items.append(f"- 类型:{mp.get('type','')} 描述:{mp.get('description','')} 数据源:{mp.get('data_source','')}")
            plan_text = f"\n## 规划的多模态元素:\n" + "\n".join(plan_items)

        hypo_text = ""
        if hypothesis_list:
            hypo_text = f"\n假设列表（用于编号一致性）:\n" + "\n".join(f"  {h}" for h in hypothesis_list)

        return f"""## 多模态增强任务
章节: {section_spec.title_cn}（{section_spec.title_en}）
章节类型: {section_spec.section_type.value}

## 需要生成的多模态元素
{chr(10).join(mm_requirements) if mm_requirements else "- 根据内容自动判断适合的多模态呈现方式"}
{plan_text}

## 研究问题
{research_question}
{hypo_text}

## 当前章节内容
{section_content[:5000]}

## 输出格式要求
对每个多模态元素，输出：
1. 元素标题（如"**图1: 研究技术路线图**"）
2. 元素内容（Mermaid代码块/LaTeX公式/表格）
3. 简要说明文字（1-2句解释该元素展示了什么）

请确保：
- Mermaid语法正确（注意节点ID不能有空格，用下划线）
- LaTeX公式完整（包含所有下标、上标、参数说明）
- 表格有明确的表头和对齐
- 不编造具体数值，用[待填充]标注
- 将多模态元素标注插入位置（用<!-- INSERT_MM_001 -->等标记）"""

    def extract_multimodal_elements(self, raw_output: str) -> List[Dict[str, str]]:
        """从输出中提取多模态元素"""
        elements = []
        lines = raw_output.split("\n")
        current_element = {"title": "", "content": "", "caption": ""}
        in_mermaid = False
        in_table = False

        for line in lines:
            if line.strip().startswith("**图") or line.strip().startswith("**表") or line.strip().startswith("**公式"):
                if current_element["content"]:
                    elements.append(current_element.copy())
                current_element = {"title": line.strip().strip("*"), "content": "", "caption": ""}
            elif "`mermaid" in line:
                in_mermaid = True
                current_element["content"] += line + "\n"
            elif in_mermaid:
                current_element["content"] += line + "\n"
                if "`" in line and "mermaid" not in line:
                    in_mermaid = False
            elif line.strip().startswith("`"):
                current_element["content"] += line + "\n"
            elif line.strip().startswith("|"):
                in_table = True
                current_element["content"] += line + "\n"
            elif in_table and not line.strip().startswith("|"):
                in_table = False

        if current_element["content"]:
            elements.append(current_element)

        return elements
