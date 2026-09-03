import sys, os, asyncio
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def diagnose():
    async with AsyncSessionLocal() as db:
        # 1. 所有表
        print('='*60)
        print('🔍 Step 1: 所有表')
        print('='*60)
        rows = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        all_tables = [r[0] for r in rows.fetchall()]
        for t in all_tables:
            print(f'   📋 {t}')

        # 2. 每个表的列 + 最新一条数据
        print(f'\n{"="*60}')
        print('🔍 Step 2: 各表结构与最新数据')
        print('='*60)
        for tbl in all_tables:
            cols = await db.execute(text(f"PRAGMA table_info({tbl})"))
            col_list = [(c[1], c[2]) for c in cols.fetchall()]
            
            count_row = await db.execute(text(f'SELECT COUNT(*) FROM [{tbl}]'))
            cnt = count_row.scalar()
            
            print(f'\n   📋 {tbl} ({cnt} rows):')
            for c, dt in col_list:
                print(f'      {c} ({dt})')
            
            if cnt > 0:
                row = await db.execute(text(f'SELECT * FROM [{tbl}] ORDER BY rowid DESC LIMIT 1'))
                data = row.fetchone()
                if data:
                    print(f'   📝 最新记录:')
                    for i, (c, dt) in enumerate(col_list):
                        val = str(data[i])[:120] if data[i] is not None else 'NULL'
                        print(f'      {c} = {val}')

        # 3. 搜索包含 "宇宙" 的所有数据
        print(f'\n{"="*60}')
        print('🔍 Step 3: 搜索包含 "宇宙" 的数据')
        print('='*60)
        for tbl in all_tables:
            cols = await db.execute(text(f"PRAGMA table_info({tbl})"))
            col_names = [c[1] for c in cols.fetchall()]
            text_cols = []
            for c in col_names:
                try:
                    r = await db.execute(text(f"SELECT [{c}] FROM [{tbl}] WHERE CAST([{c}] AS TEXT) LIKE '%宇宙%' LIMIT 1"))
                    if r.fetchone():
                        text_cols.append(c)
                except:
                    pass
            if text_cols:
                print(f'   ✅ {tbl}: 在列 {text_cols} 中找到 "宇宙"')
                for c in text_cols:
                    rows = await db.execute(text(f"SELECT rowid, [{c}] FROM [{tbl}] WHERE CAST([{c}] AS TEXT) LIKE '%宇宙%' LIMIT 3"))
                    for r in rows.fetchall():
                        print(f'      rowid={r[0]}: {str(r[1])[:150]}')

asyncio.run(diagnose())
