# -*- coding: utf-8 -*-
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("=== L1-45（imports + OUTPUT_ROOT + _check_safety）===")
for i in range(0, 45):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:170]}")

print("\n=== _build_wrapper 完整（L31-135）===")
in_bw=False
for i in range(30, 135):
    s=lines[i].strip()
    if "def _build_wrapper" in s: in_bw=True
    if in_bw: print(f"L{i+1:>3}| {lines[i].rstrip()[:150]}")
    if in_bw and s.startswith("def ") and i>31: break
