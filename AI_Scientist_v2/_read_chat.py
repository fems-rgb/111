# -*- coding: utf-8 -*-
"""看 ChatView.vue 里怎么调用"解析服务"，确认 resume/tasks 的链路"""
import re
P = r"D:\111-1\AI_Scientist_v2\frontend\src\views\chat\ChatView.vue"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(lines):
    s = l.strip()
    if re.search(r"resume|tasks|解析|parse|资源|file_parser|upload|/api/", s, re.I):
        print(f"L{i+1:>3}| {s[:180]}")
