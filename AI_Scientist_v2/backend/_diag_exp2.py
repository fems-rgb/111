# -*- coding: utf-8 -*-
"""看 _run.py 完整内容（尤其 exec 部分 + df 定义）+ 找数据集 + charts现状"""
import os, re, glob

d = r"D:\111-1\AI_Scientist_v2\backend\output\experiments\87"
run = os.path.join(d, "_run.py")
lines = open(run, encoding="utf-8", errors="ignore").read().split("\n")
print("="*70)
print(f"[1] _run.py 全文（共 {len(lines)} 行）")
print("="*70)
for i, l in enumerate(lines):
    print(f"L{i+1:>3}| {l.rstrip()[:220]}")

print("\n" + "="*70)
print("[2] charts 目录现状")
print("="*70)
cd_ = os.path.join(d, "charts")
if os.path.isdir(cd_):
    fs = [f for f in os.listdir(cd_) if f.endswith(".png")]
    print(f"  PNG 数: {len(fs)}")
    for f in sorted(fs)[:10]:
        print(f"    {f}")
else:
    print("  不存在")

print("\n" + "="*70)
print("[3] 全盘找这个实验的数据集 (.csv/.json/.parquet)")
print("="*70)
roots = [r"D:\111-1\AI_Scientist_v2\backend\output",
         r"D:\111-1\AI_Scientist_v2\backend\data"]
for root in roots:
    if not os.path.isdir(root): continue
    for fp in sorted(glob.glob(os.path.join(root, "**", "*.csv"), recursive=True))[-15:]:
        print(f"  {os.path.relpath(fp, r'D:\111-1\AI_Scientist_v2')}")
