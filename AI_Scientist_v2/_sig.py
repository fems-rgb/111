# -*- coding: utf-8 -*-
"""确认 generate_challenge_cup_pdf 的真实签名 + 所有调用点的传参"""
import glob
ROOT = r"D:\111-1\AI_Scientist_v2\backend"

# 1) 函数定义（签名）
print("="*70)
print("[1] 函数定义签名")
print("="*70)
lines = open(r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py", encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    if "def generate_challenge_cup_pdf" in l:
        print(f"  L{i+1}| {l.rstrip()}")

# 2) 所有调用点 + 前后上下文
print()
print("="*70)
print("[2] 所有调用点（含上下文）")
print("="*70)
for pat in ["**/*.py"]:
    for path in glob.glob(f"{ROOT}/{pat}", recursive=True):
        try: src = open(path, encoding="utf-8").read()
        except: continue
        if "generate_challenge_cup_pdf" in src and "def generate_challenge_cup_pdf" not in src:
            ls = src.split("\n")
            for i, l in enumerate(ls):
                if "generate_challenge_cup_pdf" in l:
                    for j in range(max(0,i-2), min(len(ls),i+2)):
                        print(f"  {path.split(chr(92))[-1]}:L{j+1}| {ls[j].rstrip()[:150]}")
                    print()
