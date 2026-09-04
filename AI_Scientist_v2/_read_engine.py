# -*- coding: utf-8 -*-
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("=== experiment_engine.py L140-235（run_experiment 主逻辑 + 返回 charts）===")
for i, l in enumerate(lines):
    if 140 <= i+1 <= 235:
        print(f"L{i+1:>3}| {l.rstrip()[:170]}")
