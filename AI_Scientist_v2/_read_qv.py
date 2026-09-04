# -*- coding: utf-8 -*-
"""看 QuestionsView.vue 报错行 + resume/tasks 调用链"""
import re
P = r"D:\111-1\AI_Scientist_v2\frontend\src\views\workspace\QuestionsView.vue"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

print("=== 报错行上下文 ===")
for n in [978, 1184, 1205, 1225, 1271]:
    print(f"\n--- L{n} ---")
    for i in range(n-3, n+2):
        if 0 <= i < len(lines):
            print(f"  L{i+1:>4}| {lines[i].rstrip()[:150]}")

print("\n=== resume / tasks / projectStore / 资源解析 相关行 ===")
for i, l in enumerate(lines):
    s = l.strip()
    if re.search(r"resume|/tasks|projectStore|useProjectStore|startGenTracking|资源|解析|parse", s, re.I):
        print(f"  L{i+1:>4}| {s[:180]}")
