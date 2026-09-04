# -*- coding: utf-8 -*-
"""
用【前端实际用的数据库】测 auto_export_pdf
先跑 _read_session.py + _find_db.py 确认 DB 路径，再改下面 REAL_DB
"""
import asyncio, traceback, os, sys

REAL_DB = r"D:\AI_Scientist\AI_Scientist\backend\zhixing.db"  # ← 如果前端用的是别的，改这里

# 临时让 session 连这个 DB
from app.database import session as sess_mod
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSessionLocal as _Base
import sqlalchemy

# 直接构造一个新 engine 指向真实 DB
real_url = f"sqlite+aiosqlite:///{REAL_DB}"
engine = create_async_engine(real_url, echo=False)
AsyncSessionLocal = sqlalchemy.orm.sessionmaker(engine, class_=sqlalchemy.ext.asyncio.AsyncSession, expire_on_commit=False)

from app.api.v1.export import auto_export_pdf

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import text
        r = await db.execute(text("SELECT COUNT(*) FROM projects"))
        print("projects 总数:", r.scalar_one())
        r = await db.execute(text("SELECT id, status, `title` FROM projects ORDER BY id DESC LIMIT 5"))
        rows = r.fetchall()
        for row in rows:
            print(f"  id={row[0]}  status={row[1]}  title={row[2]!r}")

        if rows:
            REAL_PID = rows[0][0]
            print(f"\n=== 测 auto_export_pdf(pid={REAL_PID}) ===")
            try:
                result = await auto_export_pdf(REAL_PID, db)
                print("[auto_export_pdf] 返回:", result)
                if result and os.path.isfile(result):
                    print("  大小:", os.path.getsize(result)//1024, "KB")
            except Exception as e:
                print("[异常]"); traceback.print_exc()

asyncio.run(main())
