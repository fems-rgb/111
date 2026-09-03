"""智研星枢 - 反馈反思Agent（赛道一闭环：基于实验结果迭代修正假设）"""
from app.agents.base import BaseAgent


class ReflectionAgent(BaseAgent):
    name = "reflection"
    display_name = "🔄 反馈反思Agent"
    description = "基于实验/仿真结果与人工反馈，评估假设有效性并提出迭代修正方向"
    requires_review = False
    system_prompt = """你是科研方法论与批判性思维专家。基于实验/仿真结果和反馈信息，对当前假设体系进行反思评估。
要求：
1. 逐条评估每个假设被支持/部分支持/拒绝的程度及证据强度
2. 识别结果中的异常模式、意外发现或矛盾证据
3. 提出具体的假设修正建议（细化/拆分/合并/替换）
4. 给出下一轮迭代的优先级排序与理由
5. 评估当前研究整体的闭环成熟度（0-100%）

输出格式（Markdown）：
## 反思报告
### 假设评估

| 假设 | 支持度 | 证据强度 | 状态 |
|------|--------|----------|------|
| H1   | X/10   | 强/中/弱  | 支持/部分/拒绝 |

### 关键发现与异常
- ...

### 迭代修正建议
1. **[修正动作]**：[具体建议] — 优先级：高/中/低
2. ...

### 闭环成熟度：XX%
### 下一轮重点：...
"""

    def build_prompt(self, research_question: str, context: str, **kwargs) -> str:
        feedback = kwargs.get("feedback", "")
        experiment_result = kwargs.get("experiment_result", "")
        return f"""请基于以下信息进行科研反思与迭代评估。

## 研究问题
{research_question}

## 当前假设与实验结果
{context[:4000]}

## 本轮实验/仿真结果
{experiment_result[:3000]}

## 反馈信息（人工/自动）
{feedback[:2000]}

请逐条评估假设、识别异常、提出修正建议，并给出闭环成熟度评分与下一轮重点。"""
