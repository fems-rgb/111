"""智研星枢 - 研究设计Agent"""
from app.agents.base import BaseAgent


class DesignAgent(BaseAgent):
    name = "design"
    display_name = "📐 研究设计Agent"
    description = "将研究问题转化为可检验的实证研究方案"
    requires_review = True
    system_prompt = """你是实证研究方法论专家。将研究问题转化为严谨的研究设计，包含：
1. 研究假设（3-5个，具体可操作可证伪）
2. 理论框架与概念模型
3. 数据来源与样本
4. 变量定义表
5. 计量模型（数学表达式）
6. 识别策略
7. 稳健性检验方案（≥3种）
Markdown格式。"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        return f"基于研究问题和文献综述，设计实证研究方案：\n\n## 研究问题\n{research_question}\n\n## 文献综述\n{context[:5000]}\n\n请设计完整研究方案。"