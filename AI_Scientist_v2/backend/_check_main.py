# -*- coding: utf-8 -*-
"""检查 main.py 是否有重复的 router 注册。"""
MAIN = r"D:\111-1\AI_Scientist_v2\backend\app\main.py"
lines = open(MAIN, encoding="utf-8", errors="ignore").read().splitlines()
seen = {}
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith("app.include_router(") or s.startswith("app.add_exception_handler("):
        key = s
        if key in seen:
            print(f"  L{i+1}: [重复!] {s}")
        else:
            seen[key] = i+1
            print(f"  L{i+1}: [首次] {s}")
