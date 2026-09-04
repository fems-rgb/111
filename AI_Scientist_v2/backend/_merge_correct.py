# -*- coding: utf-8 -*-
"""纠正：用【有数据的 backup 库】覆盖 111-1 的空库"""
import shutil, os

SRC = r"D:\AI_Scientist_backup\backend\zhixing.db"   # 有数据（2 个 COMPLETED 项目）
DST = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"   # 当前空的（9852KB 是错的那个）

assert os.path.exists(SRC), f"源不存在: {SRC}"
print(f"源库: {os.path.getsize(SRC)//1024} KB (有 {2} 个项目)")

shutil.copy(DST, DST + ".bak_wrong")  # 备份当前错的
shutil.copy2(SRC, DST)                 # 覆盖为有数据的
print(f"[已复制] backup → 111-1")
print(f"  新库: {os.path.getsize(DST)//1024} KB")
print("\n.env 保持: DATABASE_URL=sqlite+aiosqlite:///D:/111-1/AI_Scientist_v2/backend/zhixing.db")
