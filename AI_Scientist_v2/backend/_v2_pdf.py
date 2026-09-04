# -*- coding: utf-8 -*-
"""测试：String(32) 改动后，能否正常读出 agent_tasks 并生成 PDF"""
import asyncio, os
from app.database.session import AsyncSessionLocal
from sqlalchemy import text
from app.api.v1.export import auto_export_pdf

async def main():
    async with AsyncSessionLocal() as db:
        # 先验证能正常读（不再报枚举错误）
        r = await db.execute(text("SELECT id, status FROM agent_tasks ORDER BY id LIMIT 5"))
        print("=== agent_tasks 可读 ✅ ===")
        for rid, s in r.fetchall():
            print(f"  id={rid} status={s!r}")

        # 测试生成 PDF
        pid = (await db.execute(text("SELECT id FROM projects ORDER BY id DESC LIMIT 1"))).scalar_one()
        print(f"\n[测试] pid={pid}")
        try:
            result = await auto_export_pdf(pid, db)
            print("[auto_export_pdf] 返回:", result)
            if result and os.path.isfile(result):
                print("  大小:", os.path.getsize(result)//1024, "KB ✓")
        except Exception as e:
            import traceback; traceback.print_exc()

asyncio.run(main())
