# -*- coding: utf-8 -*-
"""验证：合并后命令行能读到 2 个真实项目"""
import asyncio
from app.database.session import AsyncSessionLocal
from sqlalchemy import text
async def main():
    async with AsyncSessionLocal() as db:
        n = (await db.execute(text("SELECT COUNT(*) FROM projects"))).scalar_one()
        print(f"projects 总数: {n}")
        for row in (await db.execute(text("SELECT id, status, `title` FROM projects ORDER BY id DESC"))).fetchall():
            print(f"  id={row[0]}  status={row[1]}  title={row[2]!r}")
asyncio.run(main())
