# -*- coding: utf-8 -*-
"""读 export.py L690-780，确认硬编码领域举例的完整上下文"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
lines = open(p, encoding="utf-8").read().split("\n")
for i in range(689, 800):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:150]))
