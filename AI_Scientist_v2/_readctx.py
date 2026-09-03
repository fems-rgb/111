# -*- coding: utf-8 -*-
"""看 challenge_cup_pdf.py 如何组装模板上下文 ctx —— 哪些字段可能带硬编码内容"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py"
lines = open(p, encoding="utf-8").read().split("\n")
print("="*70)
print("challenge_cup_pdf.py : ctx 组装（L40-120）")
print("="*70)
for i in range(39, min(130, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:140]))
