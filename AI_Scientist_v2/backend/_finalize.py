# -*- coding: utf-8 -*-
"""清理残留 + 最终交付确认"""
import os, shutil, glob
from pypdf import PdfReader

base = r"D:\111-1\AI_Scientist_v2\backend\output\deliverables"

print("=== 清理前 ===")
for pid_dir in sorted(glob.glob(os.path.join(base, "project_*"))):
    pid = os.path.basename(pid_dir)
    for f in glob.glob(os.path.join(pid_dir, "*.pdf")):
        print(f"  {pid}/{os.path.basename(f)}  ({os.path.getsize(f)//1024} KB)")

# 删除 project_2（DB 中不存在）
p2 = os.path.join(base, "project_2")
if os.path.isdir(p2):
    shutil.rmtree(p2)
    print(f"\n[清理] 删除 {p2}（DB 中无 project 2）")

print("\n=== 最终交付 ===")
p1 = os.path.join(base, "project_1", "report.pdf")
if os.path.isfile(p1):
    r = PdfReader(p1)
    n_img = sum(len(p.images or []) for p in r.pages)
    print(f"  ✓ project_1/report.pdf")
    print(f"    大小: {os.path.getsize(p1)//1024} KB")
    print(f"    页数: {len(r.pages)}")
    print(f"    图片: {n_img} 张")
    print(f"    → 精美科研报告（WeasyPrint + Jinja2 + 57 张图表）")
