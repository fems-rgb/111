# -*- coding: utf-8 -*-
"""检查 orchestrator.py L353-392 的缩进层级是否正确"""
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
lines = open(P, encoding="utf-8").read().split("\n")
print("=== L353-392（显示前导空格数）===")
for i in range(352, 392):
    l = lines[i]
    stripped = l.lstrip()
    indent = len(l) - len(stripped)
    print(f"L{i+1:>3}| (sp={indent:>2}) {stripped[:140]}")
