# -*- coding: utf-8 -*-
"""看 _build_p1_to_p20 从哪里取数据 + 是否有"从文件系统读取"的路径"""
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(lines):
    s = l.strip()
    if "_build_p1_to_p20" in s or "def _build" in s or "experiments" in s or "deliverables" in s or "from_file" in s or "json.load" in s:
        print(f"L{i+1:>3}| {s[:200]}")
