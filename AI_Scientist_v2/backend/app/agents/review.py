"""智研星枢 - 同行评审Agent"""
from app.agents.base import BaseAgent


class ReviewAgent(BaseAgent):
    name = "review"
    display_name = "🔍 同行评审Agent"
    description = "以审稿人视角评审研究成果"
    system_prompt = """你是严格的学术期刊审稿人。评审维度：
- 创新性(25%) - 严谨性(30%) - 贡献度(25%) - 规范性(20%)
输出：
1. 各维度评分（1-10分）
2. 审稿结论（接受/小修/大修/拒绝）
3. 优点（≥3条）
4. 不足（≥3条）
5. 修改建议（≥5条，具体可操作）"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        return f"以审稿人身份评审以下研究成果：\n\n## 研究问题\n{research_question}\n\n## 完整成果\n{context[:8000]}\n\n请给出详细评审意见。"