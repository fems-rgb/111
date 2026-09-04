# -*- coding: utf-8 -*-
"""验证 3：流水线完成后，report.pdf + charts 是否自动落地"""
import os
ROOT = r"D:\111-1\AI_Scientist_v2\backend\output\deliverables"
if not os.path.isdir(ROOT):
    print("deliverables 目录不存在:", ROOT); 
else:
    found = False
    for pid in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, pid)
        if not os.path.isdir(d): continue
        found = True
        print(f"=== {pid} ===")
        rp = os.path.join(d, "report.pdf")
        print(f"  report.pdf: {os.path.isfile(rp)}" + (f" ({os.path.getsize(rp)//1024} KB)" if os.path.isfile(rp) else ""))
        charts = os.path.join(d, "charts")
        print("  charts:", sorted(os.listdir(charts)) if os.path.isdir(charts) else "(无)")
    if not found:
        print("尚无 project 目录，流水线可能未跑完")
