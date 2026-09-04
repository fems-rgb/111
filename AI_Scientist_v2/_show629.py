# -*- coding: utf-8 -*-
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
lines = open(P, encoding="utf-8").read().split("\n")
print("=== L627-643（确认 dirname×4）===")
for i in range(626, 643):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:160]}")
