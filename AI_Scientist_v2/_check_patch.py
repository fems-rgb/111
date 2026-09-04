# -*- coding: utf-8 -*-
"""检查 [auto-export] 块当前状态（是否已应用三段式补丁）"""
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
lines = open(P, encoding="utf-8").read().split("\n")
for i in range(536, 562):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:160]}")
