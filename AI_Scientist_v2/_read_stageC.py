# -*- coding: utf-8 -*-
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("=== stageC 完整（L324-385）===")
for i in range(323, 385):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:170]}")
