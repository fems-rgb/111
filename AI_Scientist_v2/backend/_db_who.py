# -*- coding: utf-8 -*-
"""彻底查清：命令行 vs 前端 各自连哪个 DB"""
import os

# 1. 当前命令行实际连的 DB（用当前生效的 settings）
from app.config import settings
print("=== 命令行 settings.DATABASE_URL ===")
print(" ", settings.DATABASE_URL)

# 2. 解析出实际文件路径
from sqlalchemy.engine.url import make_url
try:
    url = make_url(settings.DATABASE_URL)
    db_path = url.database
    if not os.path.isabs(db_path):
        db_path = os.path.join(os.getcwd(), db_path)
    print(" 解析路径:", os.path.abspath(db_path))
    print(" 文件存在?", os.path.exists(os.path.abspath(db_path)), "| 大小:", os.path.getsize(os.path.abspath(db_path))//1024 if os.path.exists(os.path.abspath(db_path)) else 0, "KB")
except Exception as e:
    print(" 解析失败:", e)

# 3. 列出项目下所有 .db 及其大小
print("\n=== 项目下所有 .db 文件 ===")
ROOT = r"D:\111-1\AI_Scientist_v2"
for dp, _, fs in os.walk(ROOT):
    if "node_modules" in dp: continue
    for fn in fs:
        if fn.endswith(".db"):
            p = os.path.join(dp, fn)
            print(f"  {p}  ({os.path.getsize(p)//1024} KB)")
