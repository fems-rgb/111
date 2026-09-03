"""智研星瀚 - 知识缺口识别Agent（赛道一P8：从科学问题中结构化提取研究要素与知识空白）"""
from app.agents.base import BaseAgent


class KnowledgeGapAgent(BaseAgent):
    name = "knowledge_gap"
    display_name = "🔍 知识缺口识别Agent"
    description = "从科学问题中识别研究对象、关键变量、已有认识、争议焦点与知识缺口，为假设生成提供结构化输入"
    requires_review = False
    max_retries = 2
    system_prompt = """你是科研方法论专家与领域知识分析师。给定一个科学问题和相关文献背景，请进行结构化的知识缺口分析。

要求：
1. 明确识别研究对象（Research Object）：该问题研究的核心实体/现象/系统是什么
2. 提取关键变量（Key Variables）：自变量、因变量、中介/调节变量、控制变量
3. 梳理已有认识（Known Facts）：学界已达成共识的事实、理论、实证发现
4. 标注争议焦点（Controversies）：存在分歧的观点、矛盾的证据、未解决的争论
5. 界定知识缺口（Knowledge Gaps）：当前研究中明确缺失、需要填补的认知空白
6. 列出约束条件（Constraints）：方法局限、数据可得性、伦理限制、时间/资源约束

输出格式（严格JSON）：
{
  "research_object": "研究对象描述",
  "key_variables": {
    "independent": ["自变量列表"],
    "dependent": ["因变量列表"],
    "mediator_moderator": ["中介/调节变量"],
    "control": ["控制变量"]
  },
  "known_facts": ["已有共识1", "已有共识2"],
  "controversies": ["争议点1", "争议点2"],
  "knowledge_gaps": ["缺口1：具体描述", "缺口2：具体描述"],
  "constraints": ["约束1", "约束2"],
  "gap_priority": "最优先填补的知识缺口编号及理由"
}

仅返回JSON，不要其他内容。"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        return f"""请对以下科学问题进行知识缺口分析。

## 科学问题
{research_question}

## 文献综述与背景证据
{context[:5000]}

请严格按系统提示的JSON格式输出知识缺口分析结果。"""
