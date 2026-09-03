import asyncio, sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 直接连根目录的数据库！
DB_URL = 'sqlite+aiosqlite:///D:/AI_Scientist/AI_Scientist/backend/zhixing.db'
engine = create_async_engine(DB_URL, echo=False)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def diagnose_real_db():
    async with Session() as db:
        print('='*60)
        print('?? 诊断根目录 zhixing.db (后端实际使用的)')
        print('='*60)
        
        # 所有表及行数
        rows = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [r[0] for r in rows.fetchall()]
        print(f'\n?? 共 {len(tables)} 张表:')
        for t in tables:
            count = (await db.execute(text(f'SELECT count(*) FROM "{t}"'))).scalar()
            flag = '??' if count == 0 else '?'
            print(f'   {flag} {t}: {count} 行')
        
        # users
        print('\n?? Users:')
        rows = await db.execute(text('SELECT id, username, role, email FROM users LIMIT 5'))
        for u in rows.fetchall():
            print(f'   id={u[0]}, username={u[1]}, role={u[2]}, email={u[3]}')
        
        # projects
        print('\n?? Projects:')
        rows = await db.execute(text('SELECT id, title, owner_id, status, created_at FROM projects LIMIT 10'))
        projs = rows.fetchall()
        if not projs:
            print('   ?? 空！')
        for p in projs:
            print(f'   id={p[0]}, title={p[1]}, owner={p[2]}, status={p[3]}, created={p[4]}')
        
        # science_questions
        print('\n? Science Questions:')
        cols = await db.execute(text('PRAGMA table_info("science_questions")'))
        col_names = [c[1] for c in cols.fetchall()]
        print(f'   列名: {col_names}')
        rows = await db.execute(text(f'SELECT * FROM science_questions LIMIT 3'))
        for r in rows.fetchall():
            print(f'   {dict(zip(col_names, r))}')
        
        # question_tasks
        print('\n?? Question Tasks:')
        rows = await db.execute(text('SELECT id, question_id, status, progress, created_at FROM question_tasks ORDER BY id DESC LIMIT 5'))
        for r in rows.fetchall():
            print(f'   id={r[0]}, qid={r[1]}, status={r[2]}, progress={r[3]}, created={r[4]}')
        
        # agent_tasks
        print('\n?? Agent Tasks:')
        rows = await db.execute(text('SELECT id, project_id, agent_name, status, created_at FROM agent_tasks ORDER BY id DESC LIMIT 5'))
        tasks = rows.fetchall()
        if not tasks:
            print('   ?? 空！前端显示的27个任务是mock数据')
        for t in tasks:
            print(f'   id={t[0]}, project_id={t[1]}, agent={t[2]}, status={t[3]}, created={t[4]}')
        
        # pipeline_runs
        print('\n? Pipeline Runs:')
        rows = await db.execute(text('SELECT id, pipeline_id, status, result_summary, created_at FROM pipeline_runs ORDER BY id DESC LIMIT 5'))
        runs = rows.fetchall()
        if not runs:
            print('   ?? 空！')
        for r in runs:
            print(f'   id={r[0]}, pipeline={r[1]}, status={r[2]}, created={r[4]}')
            print(f'      result: {str(r[3])[:150] if r[3] else "NULL"}')
        
        # pipelines
        print('\n?? Pipelines:')
        rows = await db.execute(text('SELECT id, name, status, created_at FROM pipelines LIMIT 5'))
        for r in rows.fetchall():
            print(f'   id={r[0]}, name={r[1]}, status={r[2]}, created={r[3]}')

asyncio.run(diagnose_real_db())
