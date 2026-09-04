# -*- coding: utf-8 -*-
"""确认 DB 里真实的 projects 列表"""
import asyncio
from app.database.session import AsyncSessionLocal
from sqlalchemy import text
async def chk():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT p.id, p.title, p.status,
                   (SELECT COUNT(*) FROM hypotheses h WHERE h.project_id=p.id) n_hyp,
                   (SELECT COUNT(*) FROM experiment_runs e WHERE e.project_id=p.id) n_exp,
                   (SELECT COUNT(*) FROM agent_tasks a WHERE a.project_id=p.id) n_tasks
            FROM projects p ORDER BY p.id
        """))
        print("=== 所有项目 ===")
        print(f"{'id':>3} {'title':<40} {'status':<12} {'hyp':>3} {'exp':>3} {'tasks':>5}")
        for row in r.fetchall():
            print(f"{row[0]:>3} {(row[1] or '(无标题)')[:38]:<40} {(row[2] or ''):<12} {row[3]:>3} {row[4]:>3} {row[5]:>5}")
asyncio.run(chk())
