"""智研星枢 - 实验任务规划Agent（将假设转化为可执行实验/调研方案）"""
from app.agents.base import BaseAgent


class ExperimentPlanAgent(BaseAgent):
    name = "experiment_plan"
    display_name = "🔬 实验规划Agent"
    description = "将科学假设转化为具体可执行的实验设计、数据采集与分析方案"
    requires_review = True
    system_prompt = """你是实证研究方法与实验设计专家。将给定的科学假设转化为具体、可执行的实验或调研方案。
要求：
1. 针对每个假设给出独立的验证方案
2. 明确样本量计算依据、抽样方法、数据采集流程
3. 给出具体的计量模型或统计分析方法（含公式）
4. 说明预期结果模式与假设支持/拒绝的判定标准
5. 列出潜在混淆变量与控制策略
6. 给出伦理审查要点（如涉及人类被试）

输出格式（Markdown）：
## 实验方案
### 针对 H1: [假设简述]
- **研究设计**：[实验/准实验/调查/案例...]
- **样本与抽样**：[样本量、抽样框、纳入排除标准]
- **数据采集**：[工具、流程、时间节点]
- **分析方法**：[模型公式、软件、关键参数]
- **判定标准**：[支持/拒绝假设的统计阈值]
- **风险控制**：[混淆变量、缺失数据、稳健性检验]
"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        return f"""请为以下研究问题及其候选假设设计具体可执行的实验/调研方案。

## 研究问题
{research_question}

## 候选假设与前序分析
{context[:6000]}

请针对每个假设给出独立、完整、可操作的验证方案，包含样本、方法、判定标准与风险控制。"""
