# -*- coding: utf-8 -*-
"""看 TaskStatus 枚举定义 + agent_tasks 里非法的 status 值"""
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\database\models.py"
t = open(P, encoding="utf-8", errors="ignore").read()

# 找 TaskStatus 枚举
for m in re.finditer(r"class TaskStatus.*?(?=\nclass |\Z)", t, re.S):
    blk = m.group(0)
    if "TaskStatus" in blk.split("\n")[0]:
        print("=== TaskStatus 枚举 ===")
        print(blk[:800])

# 查数据库里实际的 status 值分布
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
DB = r"D:\AI_Scientist_backup\backend\zhixing.db"
e = create_async_engine(f"sqlite+aiosqlite:///{DB}", echo=False)
S = sessionmaker(e, class_=AsyncSession, expire_on_commit=False)
async def main():
    async with S() as db:
        print("\n=== agent_tasks.status 分布 ===")
        r = await db.execute(text("SELECT status, COUNT(*) c FROM agent_tasks GROUP BY status ORDER BY c DESC"))
        for row in r.fetchall():
            print(f"  {row[0]!r:20} x{row[1]}")
        print("\n=== iteration_records.status 分布 ===")
        try:
            r = await db.execute(text("SELECT status, COUNT(*) c FROM iteration_records GROUP BY status ORDER BY c DESC"))
            for row in r.fetchall():
                print(f"  {row[0]!r:20} x{row[1]}")
        except Exception as e:
            print("  (表不存在或无此列)")
asyncio.run(main())
