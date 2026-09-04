# -*- coding: utf-8 -*-
"""读 _build_wrapper / run_experiment 签名 + _auto_generate_charts 精确体（只读）"""
import os, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("="*70)
print("[1] _build_wrapper / run_experiment 签名")
print("="*70)
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith("def _build_wrapper") or s.startswith("def run_experiment") or s.startswith("async def run_experiment"):
        print(f"L{i+1:>3}| {s[:260]}")
print("\n[2] _build_wrapper 内 'exec(\"\"\"' 前后 (确认注入点)")
for i, l in enumerate(lines):
    if '"exec(' in l or 'safe_code' in l:
        print(f"L{i+1:>3}| {l.rstrip()[:260]}")
print("\n[3] run_experiment 调用 _build_wrapper 处")
for i, l in enumerate(lines):
    if '_build_wrapper(' in l and 'def ' not in l:
        print(f"L{i+1:>3}| {l.strip()[:260]}")
