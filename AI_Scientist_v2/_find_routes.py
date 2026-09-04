# -*- coding: utf-8 -*-
"""找 resume / tasks 路由定义 + 是否调用 file_parser"""
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
for dp, _, fs in os.walk(ROOT):
    if "__pycache__" in dp: continue
    for fn in fs:
        if not fn.endswith(".py"): continue
        p = os.path.join(dp, fn)
        try: t = open(p, encoding="utf-8", errors="ignore").read()
        except: continue
        if "resume" in t.lower() or "/tasks" in t or "file_parser" in t:
            print("FILE:", p.replace(ROOT,""))
            for i, l in enumerate(t.split("\n")):
                if re.search(r"resume|file_parser|parse_file|@router\.(get|post)", l, re.I):
                    print(f"  L{i+1:>3}| {l.strip()[:180]}")
