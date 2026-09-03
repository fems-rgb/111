import asyncio, sys, json
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def diagnose():
    async with AsyncSessionLocal() as db:
        print('='*60)
        print('🔍 数据库全面诊断')
        print('='*60)
        
        # 1. 所有表及行数
        tables = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        table_names = [r[0] for r in tables.fetchall()]
        print(f'\n📊 共 {len(table_names)} 张表:')
        for t in table_names:
            count = (await db.execute(text(f'SELECT count(*) FROM "{t}"'))).scalar()
            if count > 0:
                print(f'   {t}: {count} 行')
        
        # 2. projects 详情
        print('\n📁 Projects:')
        rows = await db.execute(text('SELECT id, title, owner_id, status, created_at FROM projects LIMIT 10'))
        projects = rows.fetchall()
        if not projects:
            print('   ⚠️ 空！这就是前端显示"暂无项目"的原因')
        for p in projects:
            print(f'   id={p[0]}, title={p[1]}, owner={p[2]}, status={p[3]}, created={p[4]}')
        
        # 3. questions (科学问题题库)
        print('\n❓ Questions:')
        rows = await db.execute(text('SELECT id, question_text, status, progress, project_id FROM questions LIMIT 5'))
        qs = rows.fetchall()
        for q in qs:
            print(f'   id={q[0]}, q={q[1][:30] if q[1] else "N/A"}, status={q[2]}, progress={q[3]}, project_id={q[4]}')
        
        # 4. agent_tasks
        print('\n🤖 Agent Tasks (前5):')
        rows = await db.execute(text('SELECT id, project_id, agent_name, status, created_at FROM agent_tasks ORDER BY id DESC LIMIT 5'))
        for t in rows.fetchall():
            print(f'   id={t[0]}, project_id={t[1]}, agent={t[2]}, status={t[3]}, created={t[4]}')
        
        # 5. pipeline_runs
        print('\n⚡ Pipeline Runs:')
        rows = await db.execute(text('SELECT id, pipeline_id, status, result_summary, created_at FROM pipeline_runs ORDER BY id DESC LIMIT 5'))
        for r in rows.fetchall():
            summary = str(r[3])[:80] if r[3] else 'NULL'
            print(f'   id={r[0]}, pipeline={r[1]}, status={r[2]}, result={summary}, created={r[4]}')
        
        # 6. users
        print('\n👤 Users:')
        rows = await db.execute(text('SELECT id, username, role FROM users LIMIT 5'))
        for u in rows.fetchall():
            print(f'   id={u[0]}, username={u[1]}, role={u[2]}')
        
        # 7. 检查当前登录用户的 project 查询逻辑
        print('\n🔑 关键诊断: projects 表的 owner_id vs 当前用户')
        user_rows = await db.execute(text('SELECT id, username FROM users'))
        users = user_rows.fetchall()
        proj_rows = await db.execute(text('SELECT id, owner_id FROM projects'))
        projs = proj_rows.fetchall()
        print(f'   用户IDs: {[u[0] for u in users]}')
        print(f'   项目owner_ids: {[p[1] for p in projs]}')
        if projs and users:
            owner_ids = {p[1] for p in projs}
            user_ids = {u[0] for u in users}
            if not owner_ids.intersection(user_ids):
                print('   ❌ 项目的 owner_id 和任何用户 ID 都不匹配！这就是查不到项目的原因！')

asyncio.run(diagnose())
