# -*- coding: utf-8 -*-
"""看 deliverables/project_X 目录里到底有什么文件（推断数据结构）"""
import os, json

ROOT = r"D:\111-1\AI_Scientist_v2\backend\output\deliverables"
for pid in ["project_1", "project_5", "project_20"]:
    d = os.path.join(ROOT, pid)
    print(f"=== {pid} ===")
    if not os.path.isdir(d):
        print("  (不存在)"); continue
    for root, dirs, files in os.walk(d):
        for f in sorted(files):
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, d)
            sz = os.path.getsize(fp)
            print(f"  {rel}  ({sz//1024} KB)")
            # 打印小 json/md 的前几行
            if (f.endswith(".json") or f.endswith(".md")) and sz < 50000:
                try:
                    t = open(fp, encoding="utf-8", errors="ignore").read()
                    for l in t.split("\n")[:12]:
                        print(f"    | {l[:150]}")
                except: pass
