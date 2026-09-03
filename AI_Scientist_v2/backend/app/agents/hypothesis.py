"""智研星枢 - 假设生成Agent（赛道一核心：从研究问题主动生成可检验假设）"""
from app.agents.base import BaseAgent


class HypothesisAgent(BaseAgent):
    name = "hypothesis"
    display_name = "💡 假设生成Agent"
    description = "基于研究问题与文献证据，生成2-4个相互竞争、可证伪的科学假设，并挂载证据链"
    requires_review = True
    system_prompt = """你是顶尖科学家与科研方法论专家。基于给定的研究问题和已有文献证据，提出2-4个相互竞争、可检验的科学假设。
要求：
1. 每个假设必须是可证伪的具体命题，而非泛泛建议或研究目标
2. 明确说明依据哪些事实/文献/数据（证据链）
3. 给出可操作的验证方法（实验/调查/计量模型等）
4. 假设之间应存在张力或竞争关系，避免同义重复
5. 评估每个假设的可验证性（1-10分，10=完全可实证检验）

输出格式（Markdown）：
## 候选假设
### H1: [假设陈述]
- **依据**：[文献/事实/数据摘要]
- **变量**：[自变量、因变量、控制变量]
- **验证方法**：[具体可操作方案]
- **可验证性评分**：X/10

### H2: ...
"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        return f"""请基于以下研究问题和文献综述，生成2-4个相互竞争、可证伪的科学假设。

## 研究问题
{research_question}

## 文献综述与背景证据
{context[:5000]}

请严格按系统提示的格式输出，确保每个假设都有明确的证据链和可操作验证方法。"""
