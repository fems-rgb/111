# -*- coding: utf-8 -*-
"""在 111-1 项目下找所有 .db 文件"""
import os
ROOT = r"D:\111-1\AI_Scientist_v2"
found = []
for dp, _, fs in os.walk(ROOT):
    if "__pycache__" in dp or "node_modules" in dp: continue
    for fn in fs:
        if fn.endswith(".db") or fn.endswith(".sqlite"):
            p = os.path.join(dp, fn)
            try:
                sz = os.path.getsize(p)
                found.append((p, sz))
            except: pass
print("=== 项目下的数据库文件 ===")
for p, sz in sorted(found):
    print(f"  {p}  ({sz//1024} KB)")
