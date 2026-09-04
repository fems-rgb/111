# -*- coding: utf-8 -*-
"""诊断 experiments/87/_run.py 的 df 从哪来、图表怎么生成的"""
import os, re, glob, json

print("="*70)
print("[1] experiments/87 目录内容")
print("="*70)
d = r"D:\111-1\AI_Scientist_v2\backend\output\experiments\87"
if os.path.isdir(d):
    for f in sorted(os.listdir(d)):
        fp = os.path.join(d, f)
        print(f"  {f:30} {os.path.getsize(fp)//1024:>5} KB" + ("  [DIR]" if os.path.isdir(fp) else ""))
else:
    print("  ❌ 目录不存在，搜索其他 experiment 目录...")
    base = r"D:\111-1\AI_Scientist_v2\backend\output\experiments"
    if os.path.isdir(base):
        for x in sorted(os.listdir(base))[-5:]:
            print(f"    {x}")

print("\n" + "="*70)
print("[2] _run.py 内容（重点看 df 哪来的、图表代码）")
print("="*70)
run = os.path.join(d, "_run.py")
if os.path.isfile(run):
    lines = open(run, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(lines[:60]):
        print(f"L{i+1:>3}| {l.rstrip()[:200]}")
    # 统计 df 出现位置
    print("\n--- df 相关行 ---")
    for i, l in enumerate(lines):
        if re.search(r"\bdf\b", l):
            print(f"L{i+1:>3}| {l.rstrip()[:200]}")
