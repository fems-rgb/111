# -*- coding: utf-8 -*-
P = r"D:\111-1\AI_Scientist_v2\backend\app\services\file_parser.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("=== file_parser.py（前60行：路由/入口/错误文案）===")
for i in range(0, 60):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:170]}")
