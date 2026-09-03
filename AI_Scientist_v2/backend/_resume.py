import sys, os, asyncio
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def resume():
    async with AsyncSessionLocal() as db:
        # 1. 将 project 状态从 PAUSED 改回 RUNNING
        await db.execute(text("UPDATE projects SET status = 'RUNNING' WHERE id = 1"))
        
        # 2. 将 question_tasks 的 progress 重置（可选，保持 running）
        await db.execute(text("UPDATE question_tasks SET status = 'running' WHERE id = 1"))
        
        await db.commit()
        
        # 3. 验证
        row = await db.execute(text("SELECT id, title, status FROM projects WHERE id = 1"))
        p = row.fetchone()
        print(f'✅ Project #{p[0]}: {p[1]} -> status={p[2]}')
        
        row2 = await db.execute(text("SELECT id, status, progress FROM question_tasks WHERE id = 1"))
        t = row2.fetchone()
        print(f'✅ QuestionTask #{t[0]}: status={t[1]}, progress={t[2]}')
        
        # 4. 确认待执行的 tasks
        rows = await db.execute(text("""
            SELECT id, agent_name, step_order, status 
            FROM agent_tasks 
            WHERE project_id = 1 AND status = 'PENDING'
            ORDER BY step_order
        """))
        pending = rows.fetchall()
        print(f'\n📋 待执行任务 ({len(pending)} 个):')
        for r in pending:
            print(f'   Task#{r[0]} | {r[1]:20s} | step={r[2]} | status={r[3]}')

asyncio.run(resume())
