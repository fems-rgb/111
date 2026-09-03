import asyncio
from sqlalchemy import text
from app.database.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        # 查看所有当前状态
        rows = (await db.execute(text('SELECT id, title, status FROM projects'))).fetchall()
        print('=== CURRENT ===')
        for r in rows:
            print(f'  id={r[0]}, title={r[1]}, status={r[2]}')

        # 把小写改回大写
        await db.execute(text("UPDATE projects SET status='COMPLETED' WHERE status='completed'"))
        await db.execute(text("UPDATE projects SET status='DRAFT' WHERE status='draft'"))
        await db.execute(text("UPDATE projects SET status='PLANNING' WHERE status='planning'"))
        await db.execute(text("UPDATE projects SET status='RUNNING' WHERE status='running'"))
        await db.execute(text("UPDATE projects SET status='PAUSED' WHERE status='paused'"))
        await db.commit()

        # 验证
        rows = (await db.execute(text('SELECT id, title, status FROM projects'))).fetchall()
        print('=== FIXED ===')
        for r in rows:
            print(f'  id={r[0]}, title={r[1]}, status={r[2]}')

asyncio.run(main())
