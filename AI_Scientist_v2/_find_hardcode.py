# -*- coding: utf-8 -*-
"""定位 challenge_cup 报告里「硬编码/与题目无关」文字的来源"""
import os, re

ROOT = r"D:\111-1\AI_Scientist_v2\backend"

# 1) 模板里写死的字符串
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
print("="*70)
print("[1] 模板里的「固定文案」（非 {{ }} 插值的部分）")
print("="*70)
lines = open(TPL, encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    s = l.strip()
    # 找出不是 Jinja 表达式、但含实质中文的行
    if ("{{" in s or "{%" in s or "<" in s):
        continue
    if re.search(r"[\u4e00-\u9fa5]{4,}", s):
        print("  L%d| %s" % (i+1, s[:130]))
