"""智研星枢 - 数据分析Agent"""
from app.agents.base import BaseAgent


class AnalysisAgent(BaseAgent):
    name = "analysis"
    display_name = "📊 数据分析Agent"
    description = "制定数据分析方案并提供可运行的代码框架"
    system_prompt = """你是数据科学家。制定详细的数据分析执行计划，包含：
1. 数据准备（清洗规则、变量构建、描述性统计）
2. 主回归分析代码（pandas/statsmodels）
3. 稳健性检验代码（≥3种）
4. 可视化方案代码
5. 结果解读模板
Python代码，可运行，有详细注释。"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        return f"基于研究设计，制定数据分析执行计划：\n\n## 研究问题\n{research_question}\n\n## 研究设计\n{context[:5000]}\n\n请提供完整Python分析代码。"