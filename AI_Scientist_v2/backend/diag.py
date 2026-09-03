import asyncio
from sqlalchemy import text
from app.database.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        tables = (await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))).fetchall()
        print('=== ALL TABLES ===')
        for t in tables:
            print(f'  {t[0]}')
            cols = (await db.execute(text(f'PRAGMA table_info({t[0]})'))).fetchall()
            for c in cols:
                print(f'    col: {c[1]} ({c[2]})')

asyncio.run(main())
