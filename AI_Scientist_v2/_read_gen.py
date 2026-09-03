# -*- coding: utf-8 -*-
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py"
lines = open(P, encoding="utf-8").read().split("\n")
print("=== L230-350（generate 函数：自动存文件的完整逻辑）===")
for i in range(229, min(350, len(lines))):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:150]}")
