# -*- coding: utf-8 -*-
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\writing.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
print("=== L135-175（字段11 完整要求 + build_prompt 签名）===")
for i in range(134, 175):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:170]}")
