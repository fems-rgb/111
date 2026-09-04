# -*- coding: utf-8 -*-
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\writing.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("=== writing.py 函数结构 + 字段11/可视化相关行 ===")
for i, l in enumerate(lines):
    s = l.strip()
    if re.search(r"^def |^async def |prompt|字段11|可视化|图表|figure|chart|Results|results|字段10|experiments", s, re.I) and s:
        print(f"L{i+1:>3}| {s[:150]}")
