# -*- coding: utf-8 -*-
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py"
lines = open(p, encoding="utf-8").read().split("\n")
print("L1-83 全文:")
for i in range(83):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:160]))
