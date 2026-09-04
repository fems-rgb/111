# -*- coding: utf-8 -*-
"""方案 B：把老库数据合并到 111-1 新位置（前后端统一连一个库）"""
import shutil, os

OLD = r"D:\AI_Scientist\AI_Scientist\backend\zhixing.db"   # 前端用的，有数据
NEW = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"        # 当前空的，要被覆盖

# 安全校验：老库必须存在且有数据
assert os.path.exists(OLD), f"老库不存在: {OLD}"
assert os.path.getsize(OLD) > 1024, f"老库太小: {OLD}"

# 备份当前新库（即使是空的也备份）
if os.path.exists(NEW):
    shutil.copy(NEW, NEW + ".bak_empty")
    print(f"[备份] {os.path.basename(NEW)}.bak_empty ({os.path.getsize(NEW)//1024} KB)")

# 把老库复制为新库位置
shutil.copy2(OLD, NEW)
print(f"[已复制] 老库 → 新位置")
print(f"  新库大小: {os.path.getsize(NEW)//1024} KB")

# .env 保持指向 111-1（不用改）
print("\n[.env 保持不变] DATABASE_URL=sqlite+aiosqlite:///D:/111-1/AI_Scientist_v2/backend/zhixing.db")
print("→ 前端和命令行现在连同一个库")
