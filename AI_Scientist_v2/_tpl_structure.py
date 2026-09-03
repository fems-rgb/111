# -*- coding: utf-8 -*-
"""分析模板结构：哪些标题是静态写死的，哪些是 Jinja 循环动态生成的"""
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(TPL, encoding="utf-8").read().split("\n")

print("="*70)
print("[1] 模板里所有「标题级」行（h1/h2/h3 及 一二三四五 章节）")
print("="*70)
import re
for i, l in enumerate(lines):
    s = l.strip()
    # h1/h2/h3 标签，或 一、二、三 等章节，或 2.1/3.2 等
    if re.search(r"<h[1-6]", s) or re.search(r"[一二三四五六七八九十]、", s) or re.search(r"\d+\.\d+\s", s):
        # 提取文本
        txt = re.sub(r"<[^>]+>", "", s).strip()
        if txt:
            print(f"  L{i+1}| {txt[:80]}")

print()
print("="*70)
print("[2] 模板里的 Jinja for 循环（动态区块）")
print("="*70)
for i, l in enumerate(lines):
    s = l.strip()
    if "{% for" in s or "{% if" in s or "{% block" in s:
        print(f"  L{i+1}| {s[:120]}")
