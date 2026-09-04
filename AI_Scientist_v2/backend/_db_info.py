# -*- coding: utf-8 -*-
"""查数据库文件路径 + 所有表 + project 总数"""
import asyncio, os
from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    # 找数据库文件
    from app.database.session import engine
    print("=== engine.url ===")
    print(" ", engine.url)
    url = str(engine.url)
    if url.startswith("sqlite"):
        db_path = url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if db_path == ":memory:":
            print("  (内存数据库!)")
        else:
            print("  文件:", os.path.abspath(db_path))
            print("  存在?", os.path.exists(db_path), " 大小:", os.path.getsize(db_path) if os.path.exists(db_path) else 0)

    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT COUNT(*) FROM projects"))
        print("\n=== projects 总数 ===")
        print("  count =", r.scalar_one())

        # 看有哪些表
        r = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in r.fetchall()]
        print("\n=== 所有表 ===")
        for t in sorted(tables):
            print("  ", t)

asyncio.run(main())
