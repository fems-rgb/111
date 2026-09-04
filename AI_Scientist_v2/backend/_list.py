# -*- coding: utf-8 -*-
"""列出 projects 表真实列（先看结构，再查数据）"""
import asyncio
from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        # 先看表结构
        r = await db.execute(text("PRAGMA table_info(projects)"))
        cols = [row[1] for row in r.fetchall()]
        print("=== projects 列 ===")
        print(" ", cols)
        # 用真实列名查
        if "title" in cols:
            name_col = "title"
        elif "name" in cols:
            name_col = "name"
        else:
            name_col = cols[1]  #  fallback：用第二列
        sql = f"SELECT id, status, `{name_col}` FROM projects ORDER BY id DESC LIMIT 10"
        print("\nSQL:", sql)
        r = await db.execute(text(sql))
        rows = r.fetchall()
        print("=== projects 数据 ===")
        for row in rows:
            print(f"  id={row[0]}  status={row[1]}  {name_col}={row[2]!r}")

asyncio.run(main())
