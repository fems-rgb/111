# -*- coding: utf-8 -*-
"""读模板 CSS 段落样式"""
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(TPL, encoding="utf-8").read().split("\n")

print("="*70)
print("[1] style 块里的 p / 段落 / 缩进相关样式")
print("="*70)
in_style = False
for i, l in enumerate(lines):
    s = l.strip()
    if "<style" in s: in_style = True
    if "</style>" in s:
        in_style = False
        continue
    if in_style and ("p " in s or "p{" in s or "paragraph" in s or "indent" in s or
                     "line-height" in s or "text-align" in s or "margin" in s):
        print(f"  L{i+1}| {s[:150]}")

print()
print("="*70)
print("[2] body / 正文容器 / @page 样式")
print("="*70)
in_style = False
for i, l in enumerate(lines):
    s = l.strip()
    if "<style" in s: in_style = True
    if "</style>" in s:
        in_style = False
        continue
    if in_style and ("body" in s or "main" in s or "content" in s or "section" in s or "@page" in s):
        print(f"  L{i+1}| {s[:150]}")
