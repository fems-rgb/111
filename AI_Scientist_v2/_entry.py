# -*- coding: utf-8 -*-
import re
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py"
lines = open(P, encoding="utf-8").read().split("\n")
# 找入口函数定义 + 路由装饰器 + export/download 相关
for i, l in enumerate(lines):
    s = l.rstrip()
    if re.match(r"^(def |@)", s) or re.search(r"export|download|generate|route|pdf", s, re.I):
        if s.strip():
            print(f"L{i+1:>3}| {s[:160]}")
