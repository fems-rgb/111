import asyncio
from sqlalchemy import text
from app.database.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        # 查看当前项目状态
        rows = (await db.execute(text('SELECT id, title, status, progress FROM projects'))).fetchall()
        print('=== BEFORE FIX ===')
        for r in rows:
            print(f'  id={r[0]}, title={r[1]}, status={r[2]}, progress={r[3]}')

        # 统一状态为小写（匹配枚举值）
        await db.execute(text("UPDATE projects SET status='completed' WHERE status='COMPLETED'"))
        await db.execute(text("UPDATE projects SET status='draft' WHERE status='DRAFT'"))
        await db.commit()

        # 验证
        rows = (await db.execute(text('SELECT id, title, status, progress FROM projects'))).fetchall()
        print('=== AFTER FIX ===')
        for r in rows:
            print(f'  id={r[0]}, title={r[1]}, status={r[2]}, progress={r[3]}')

asyncio.run(main())
