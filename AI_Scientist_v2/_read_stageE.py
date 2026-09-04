# -*- coding: utf-8 -*-
import os
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
P = os.path.join(ROOT, r"app\api\v1\export.py")
lines = open(P, encoding="utf-8").read().split("\n")
print("=== export.py L625-653（图表兜底逻辑完整上下文）===")
for i in range(624, 653):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:160]}")
