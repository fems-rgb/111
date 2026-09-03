# -*- coding: utf-8 -*-
"""定位 _verify_final.html 里 CMB / 大尺度结构 的上下文，确认是模板硬编码还是数据"""
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(TPL, encoding="utf-8").read().split("\n")

print("="*70)
print("[1] 模板里含 CMB / 大尺度结构 / 宇宙 的行")
print("="*70)
for i, l in enumerate(lines):
    s = l.strip()
    if any(k in s for k in ["CMB", "大尺度", "宇宙", "暗物质", "WIMP", "Planck", "SDSS", "XENON"]):
        if "{{" in s or "{%" in s:
            continue  # Jinja 变量不算
        print(f"  L{i+1}| {s[:140]}")

print()
print("="*70)
print("[2] 渲染结果 _verify_final.html 里含 CMB 的上下文")
print("="*70)
html = open(r"D:\111-1\AI_Scientist_v2\_verify_final.html", encoding="utf-8").read()
import re
# 找 CMB 前后各 60 字符
for m in re.finditer(r".{0,60}CMB.{0,60}", html):
    print("  ...", m.group()[:150], "...")
for m in re.finditer(r".{0,60}大尺度结构.{0,60}", html):
    print("  ...", m.group()[:150], "...")
