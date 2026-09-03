# -*- coding: utf-8 -*-
import os
BASE = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1"
for f in ("challenge_cup_pdf.py",):
    p = os.path.join(BASE, f)
    print("="*70)
    print(p)
    print("="*70)
    print("exists:", os.path.exists(p))
# 找前端导出按钮相关 + 后端路由
ROOT = r"D:\111-1\AI_Scientist_v2"
for dirpath, _, files in os.walk(ROOT):
    if any(x in dirpath for x in ("node_modules","__pycache__",".git","dist","build")):
        continue
    for fn in files:
        if fn.endswith((".py",".tsx",".ts",".jsx",".js")) and "challenge" in fn.lower():
            print(os.path.join(dirpath,fn))
