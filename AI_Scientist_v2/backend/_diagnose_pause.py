import sys, os, asyncio, json, traceback
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from sqlalchemy import select, text

async def diagnose():
    async with AsyncSessionLocal() as db:
        # 1. 找到这个任务
        print('='*60)
        print('🔍 Step 1: 查找 "宇宙由什么构成" 的任务记录')
        print('='*60)
        
        rows = await db.execute(text("""
            SELECT id, question_id, status, current_step, pipeline_type, 
                   error_message, created_at, updated_at
            FROM question_tasks 
            WHERE title LIKE '%宇宙%' OR question_title LIKE '%宇宙%'
            ORDER BY updated_at DESC LIMIT 5
        """))
        tasks = rows.fetchall()
        
        if not tasks:
            # 尝试其他表名/字段
            print('   question_tasks 未找到，尝试搜索所有相关表...')
            tables = await db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            for t in tables.fetchall():
                print(f'   📋 表: {t[0]}')
            
            # 尝试 science_questions 关联
            rows2 = await db.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE '%task%' OR table_name LIKE '%pipeline%' OR table_name LIKE '%run%'
            """))
            print(f'\n   任务相关表:')
            for r in rows2.fetchall():
                print(f'      {r[0]}')
        else:
            for t in tasks:
                print(f'   Task ID={t[0]}, qid={t[1]}, status={t[2]}, step={t[3]}, type={t[4]}')
                print(f'   error: {t[5]}')
                print(f'   created: {t[6]}, updated: {t[7]}')
                print()

        # 2. 查看 pipeline steps / agent runs 表
        print('='*60)
        print('🔍 Step 2: 查看所有表结构')
        print('='*60)
        tables = await db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' ORDER BY table_name
        """))
        all_tables = [r[0] for r in tables.fetchall()]
        for t in all_tables:
            print(f'   📋 {t}')

        # 3. 查看每个表的列
        print(f'\n{"="*60}')
        print('🔍 Step 3: 关键表的列信息')
        print('='*60)
        for tbl in ['question_tasks', 'pipeline_runs', 'agent_runs', 'pipeline_steps', 'research_runs']:
            if tbl in all_tables:
                cols = await db.execute(text(f"""
                    SELECT column_name, data_type FROM information_schema.columns 
                    WHERE table_name = '{tbl}' ORDER BY ordinal_position
                """))
                col_list = [(c[0], c[1]) for c in cols.fetchall()]
                print(f'\n   📋 {tbl}:')
                for c, dt in col_list:
                    print(f'      {c} ({dt})')
                
                # 取最近一条数据
                row = await db.execute(text(f'SELECT * FROM {tbl} ORDER BY 1 DESC LIMIT 1'))
                data = row.fetchone()
                if data:
                    print(f'   📝 最新记录:')
                    for i, (c, dt) in enumerate(col_list):
                        val = str(data[i])[:100] if data[i] is not None else 'NULL'
                        print(f'      {c} = {val}')

asyncio.run(diagnose())
