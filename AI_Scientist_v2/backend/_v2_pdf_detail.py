# -*- coding: utf-8 -*-
"""详细测试 PDF 生成：打印图表收集日志，看图表是否被包含"""
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")

import asyncio, os
from app.database.session import AsyncSessionLocal
from sqlalchemy import text
from app.api.v1.export import auto_export_pdf

async def main():
    async with AsyncSessionLocal() as db:
        pid = 1
        # 清空旧文件，方便观察
        import glob
        for f in glob.glob(r"D:\111-1\AI_Scientist_v2\backend\output\pdf_reports\*.pdf"):
            os.remove(f)
        
        print(f"[测试] pid={pid}")
        result = await auto_export_pdf(pid, db)
        print(f"\n[结果] {result}")
        if result and os.path.isfile(result):
            print(f"  大小: {os.path.getsize(result)//1024} KB")

asyncio.run(main())
