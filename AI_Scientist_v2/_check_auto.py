# -*- coding: utf-8 -*-
import os
DIR = r"D:\111-1\AI_Scientist_v2\backend\output\pdf_reports"
print("=== output/pdf_reports 目录 ===")
print("存在:", os.path.exists(DIR))
if os.path.exists(DIR):
    files = sorted(os.listdir(DIR))
    print("文件数:", len(files))
    for f in files[-10:]:
        fp = os.path.join(DIR, f)
        print(f"  {f}  ({os.path.getsize(fp)//1024} KB, {os.path.getmtime(fp)})")
else:
    # 可能路径不同，搜一下所有 .pdf
    ROOT = r"D:\111-1\AI_Scientist_v2"
    print("\n全盘搜索 challenge_cup*.pdf：")
    n = 0
    for dp, _, fs in os.walk(ROOT):
        if any(x in dp for x in ("node_modules","__pycache__",".git")): continue
        for f in fs:
            if f.startswith("challenge_cup") and f.endswith(".pdf"):
                fp = os.path.join(dp, f)
                print(f"  {fp}  ({os.path.getsize(fp)//1024} KB)")
                n += 1
                if n >= 15: break
