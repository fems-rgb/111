# -*- coding: utf-8 -*-
"""修复 proposal_addon.py 硬编码宇宙学术语"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\proposal_addon.py"
src = open(p, encoding="utf-8").read()

fixes = [
    ("系统围绕该问题链接 XENON、Planck、SDSS、LHC",
     "系统围绕该问题链接相关公开观测与实验数据集"),
    ("CMB 功率谱图、星系旋转曲线、实验图表",
     "领域典型观测图表与实验图表"),
]
for old, new in fixes:
    if old in src:
        src = src.replace(old, new, 1); print("[修改]", old[:30])
    else:
        print("[跳过]", old[:35])

open(p, "w", encoding="utf-8").write(src)
import py_compile
try:
    py_compile.compile(p, doraise=True); print("[syntax] OK")
except py_compile.PyCompileError as e:
    print(f"[syntax] L{e.lineno}: {e.msg}")
