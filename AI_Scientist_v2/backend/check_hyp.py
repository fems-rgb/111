import asyncio
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.models import Hypothesis, AgentTask

async def main():
    async with AsyncSessionLocal() as db:
        r = (await db.execute(select(Hypothesis).where(Hypothesis.project_id == 1))).scalars().all()
        print('假设条数:', len(r))
        for h in r:
            print(' -', h.hypo_id, '|', (h.statement or '')[:50], '| score=', h.testability_score)
        print()
        print('--- AgentTask 模型调用统计（前端成本分析数据源）---')
        t = (await db.execute(select(AgentTask).where(AgentTask.project_id == 1))).scalars().all()
        tt = 0
        tc = 0.0
        for a in t:
            print(' -', a.agent_name, '| model=', a.model_used, '| tokens=', a.tokens_used, '| cost=', a.cost_yuan)
            tt += (a.tokens_used or 0)
            tc += float(a.cost_yuan or 0)
        print('合计 tokens=', tt, '| cost=', round(tc, 4))

asyncio.run(main())