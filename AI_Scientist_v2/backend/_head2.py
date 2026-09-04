# -*- coding: utf-8 -*-
"""看 models.py 的 import 区 + 是否有循环导入"""
P = r"D:\111-1\AI_Scientist_v2\backend\app\database\models.py"
lines = open(P, encoding="utf-8").read().split("\n")
print("=== models.py 前 65 行 ===")
for i, l in enumerate(lines[:65]):
    print(f"L{i+1:>3}| {l}")

# 看 L62 User 类附近的 Base 定义
print("\n=== 搜索 'Base' / 'declarative_base' 定义 ===")
for i, l in enumerate(lines):
    if "Base" in l and ("=" in l or "class" in l or "declarative" in l):
        print(f"L{i+1:>3}| {l.strip()[:200]}")
