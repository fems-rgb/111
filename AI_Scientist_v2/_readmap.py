# -*- coding: utf-8 -*-
"""读 export.py L785-830，看 _MAP/_VC 映射表怎么用，决定如何通用化"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
lines = open(p, encoding="utf-8").read().split("\n")
for i in range(784, 835):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:160]))
