# -*- coding: utf-8 -*-
"""为 project 1、2 生成 PDF 并落地到 deliverables/project_{id}/report.pdf"""
import asyncio, os, shutil
from app.database.session import AsyncSessionLocal
from sqlalchemy import text
from app.api.v1.export import auto_export_pdf

async def main():
    async with AsyncSessionLocal() as db:
        for pid in [1, 2]:
            row = (await db.execute(text("SELECT id FROM projects WHERE id=:p"), {"p": pid})).fetchone()
            if not row:
                print(f"pid={pid} 不存在"); continue
            try:
                result = await auto_export_pdf(pid, db)
                print(f"pid={pid} -> {result}")
                if result and os.path.isfile(result):
                    dst_dir = rf"D:\111-1\AI_Scientist_v2\backend\output\deliverables\project_{pid}"
                    os.makedirs(dst_dir, exist_ok=True)
                    dst = os.path.join(dst_dir, "report.pdf")
                    shutil.copy2(result, dst)
                    print(f"  ✓ 落地: {dst} ({os.path.getsize(dst)//1024} KB)")
            except Exception as e:
                import traceback; traceback.print_exc()

asyncio.run(main())
