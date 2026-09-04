# -*- coding: utf-8 -*-
"""用真实 project_id 测 auto_export_pdf（动态取列名，不硬编码 name/title）"""
import asyncio, traceback, os
REAL_PID = 1   # ← 改成 _list.py 输出的真实 id

from app.database.session import AsyncSessionLocal
from sqlalchemy import text
from app.api.v1.export import auto_export_pdf

async def main():
    async with AsyncSessionLocal() as db:
        # 动态取主键列名（通常是 id）
        r = await db.execute(text("PRAGMA table_info(projects)"))
        cols = [row[1] for row in r.fetchall()]
        name_col = "title" if "title" in cols else ("name" if "name" in cols else cols[1])
        print("[列] id / status /", name_col)

        row = (await db.execute(
            text(f"SELECT id, status, `{name_col}` FROM projects WHERE id = :pid"),
            {"pid": REAL_PID}
        )).fetchone()
        print(f"[检查] project {REAL_PID} 存在?", row is not None, "|", dict(row) if row else None)
        if not row:
            print("→ 不存在，auto_export_pdf 会返回 None")
            return
        try:
            result = await auto_export_pdf(REAL_PID, db)
            print("[auto_export_pdf] 返回:", result)
            if result and os.path.isfile(result):
                print("  文件大小:", os.path.getsize(result)//1024, "KB")
        except Exception as e:
            print("[异常]"); traceback.print_exc()

asyncio.run(main())
