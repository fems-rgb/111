# -*- coding: utf-8 -*-
import re
# 看 writing.py 的可视化相关 prompt 段落（L120-160）
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\writing.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(lines):
    if 100 <= i+1 <= 170:
        print(f"L{i+1:>3}| {l.rstrip()[:170]}")

print("\n=== experiment_engine.py 内置可视化模板代码（给 writing 参考的绘图片段）===")
P2 = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
t2 = open(P2, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(t2):
    if 260 <= i+1 <= 370:
        print(f"L{i+1:>3}| {l.rstrip()[:150]}")
