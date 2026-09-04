# -*- coding: utf-8 -*-
"""读 experiment_engine 模板 + _gather 完整逻辑（只读）"""
import os

def dump(P, ranges):
    if not os.path.exists(P):
        print(f"  ❌ {P} 不存在"); return
    lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"\n### {os.path.relpath(P, r'D:\111-1\AI_Scientist_v2')} ({len(lines)}行) ###")
    for (a, b) in ranges:
        print(f"--- L{a}~L{b} ---")
        for i in range(a-1, min(b, len(lines))):
            print(f"L{i+1:>3}| {lines[i].rstrip()[:250]}")

P1 = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
P2 = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"

print("="*70)
print("[A] experiment_engine.py: 样板模板 + _auto_generate_charts + data_table/result_data 注入")
print("="*70)
dump(P1, [(40, 145), (145, 260), (300, 430)])

print("="*70)
print("[B] export.py L405-480: _gather 图表收集完整逻辑（glob + project过滤?）")
print("="*70)
dump(P2, [(405, 480)])
