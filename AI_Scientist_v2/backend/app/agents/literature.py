"""智研星枢 - 文献综述Agent"""
from app.agents.base import BaseAgent


class LiteratureAgent(BaseAgent):
    name = "literature"
    display_name = "📖 文献综述Agent"
    description = "系统梳理研究问题的文献脉络、理论基础和研究空白"
    requires_review = True
    system_prompt = """你是资深人文社科学者。对研究问题进行系统文献综述，输出包含：
1. 核心概念界定（中英文对照）
2. 理论基础（至少3个框架，含代表学者和核心观点）
3. 研究脉络（按时间线梳理）
4. 研究空白分析
5. 本研究学术定位
Markdown格式，每部分300-500字。"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        p = f"请对以下研究问题进行系统文献综述：\n\n## 研究问题\n{research_question}"
        p += "\n\n## 输出要求\n1.核心概念界定 2.理论基础(≥3个) 3.研究脉络 4.研究空白 5.本研究定位"
        if context:
            p += f"\n\n## 已有上下文\n{context[:3000]}"
        return p