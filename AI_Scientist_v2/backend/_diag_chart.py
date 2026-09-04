# -*- coding: utf-8 -*-
"""读图表生成器 + 图表收集逻辑 + experiment→project 映射"""
import os, re

print("="*70)
print("[1] generate_challenge_cup_pdf 里的 _gather / charts glob")
print("="*70)
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(lines):
    if 390 <= i+1 <= 500:
        if any(k in l for k in ["_gather","charts","experiments","_all_png","_pat","_root","def _","glob(","_run.py","def generate"]):
            print(f"L{i+1:>3}| {l.rstrip()[:240]}")

print("\n" + "="*70)
print("[2] 谁生成 _run.py（写图表样板/exec 的地方）")
print("="*70)
root = r"D:\111-1\AI_Scientist_v2\backend\app"
for dirpath, _, files in os.walk(root):
    if "__pycache__" in dirpath: continue
    for f in files:
        if not f.endswith(".py"): continue
        fp = os.path.join(dirpath, f)
        t = open(fp, encoding="utf-8", errors="ignore").read()
        for i, l in enumerate(t.split("\n")):
            if any(k in l for k in ["_CHARTS","_auto_save_animations","_run.py","def _run","write_text","_save = plt","data_table","result_data"]) and "print" not in l:
                print(f"{os.path.relpath(fp, r'D:\111-1\AI_Scientist_v2')}:{i+1}  {l.strip()[:220]}")
