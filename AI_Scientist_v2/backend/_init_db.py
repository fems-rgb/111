import asyncio, sys
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import engine, Base
# 确保所有 model 被 import，这样 Base.metadata 才完整
from app.database import models  # noqa

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ All tables created successfully')

    # 验证
    import sqlite3
    c = sqlite3.connect(r'D:\AI_Scientist\AI_Scientist\backend\zhixing.db')
    tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f'Tables in DB: {sorted(tables)}')
    c.close()

asyncio.run(init())
