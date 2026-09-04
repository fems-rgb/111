# -*- coding: utf-8 -*-
"""直接调用 generate_challenge_cup_pdf（WeasyPrint + 图表），看能不能出精美 PDF"""
import asyncio, os, glob
from app.database.session import AsyncSessionLocal
from app.api.v1.export import generate_challenge_cup_pdf

async def main():
    async with AsyncSessionLocal() as db:
        # 先清空旧 PDF
        for f in glob.glob(r"D:\111-1\AI_Scientist_v2\backend\output\pdf_reports\*.pdf"):
            try: os.remove(f)
            except Exception: pass

        for pid in [1, 2]:
            print(f"\n=== pid={pid} 调用 generate_challenge_cup_pdf ===")
            try:
                result = generate_challenge_cup_pdf(pid)
                # 可能是同步函数，也可能内部用 loop
                if asyncio.iscoroutine(result):
                    result = await result
                print(f"  返回: {result}")
                if result and os.path.isfile(result):
                    print(f"  大小: {os.path.getsize(result)//1024} KB")
            except Exception as e:
                import traceback; traceback.print_exc()

asyncio.run(main())
