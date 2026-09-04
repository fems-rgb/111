# -*- coding: utf-8 -*-
"""wire_final2.py - 精确接线: RunRequest加data_table + _exec透传 + orchestrator补meta。"""
import os, re, ast, shutil

ROOT=r"D:\111-1\AI_Scientist_v2"

def backup(P):
    if not os.path.exists(P+".wire_bak"):
        shutil.copy(P, P+".wire_bak"); print(f"  [备份] {os.path.basename(P)}.wire_bak")

def check(P):
    ast.parse(open(P,encoding="utf-8",errors="ignore").read())
    print(f"  [OK] SYNTAX {os.path.basename(P)}")

lab=os.path.join(ROOT,r"backend\app\api\v1\experiment_lab.py")
orc=os.path.join(ROOT,r"backend\app\agents\orchestrator.py")

# ==================== 1) experiment_lab.py ====================
print("=== experiment_lab.py ===")
backup(lab)
t=open(lab,encoding="utf-8",errors="ignore").read()

# 1a) RunRequest 加 data_table 字段 (在 code: str 行后, 或类内任意位置)
if "data_table" not in t.split("class RunRequest")[1].split("class ")[0]:
    # 在 "code: str" 后加一行
    t=t.replace("    code: str\n", "    code: str\n    data_table: dict | None = None  # 前端传的真实数据\n", 1)
    print("  [1a] RunRequest 加 data_table 字段")
else:
    print("  [1a] RunRequest 已有 data_table, 跳过")

# 1b) _exec 签名加 data_table=None
old_sig="async def _exec(run_id, code, timeout, gen_video):"
new_sig="async def _exec(run_id, code, timeout, gen_video, data_table=None):"
if old_sig in t:
    t=t.replace(old_sig, new_sig)
    print("  [1b] _exec 签名加 data_table=None")
elif "async def _exec(run_id, code, timeout, gen_video, data_table=None):" in t:
    print("  [1b] _exec 签名已有 data_table, 跳过")
else:
    print("  [!!][1b] 未匹配 _exec 签名, 请手动改")

# 1c) bg.add_task 加 req.data_table
old_bg="bg.add_task(_exec, run.id, req.code, req.timeout, req.generate_video)"
new_bg="bg.add_task(_exec, run.id, req.code, req.timeout, req.generate_video, req.data_table)"
if old_bg in t:
    t=t.replace(old_bg, new_bg)
    print("  [1c] bg.add_task 传 req.data_table")
elif "req.data_table" in t:
    print("  [1c] bg.add_task 已传 data_table, 跳过")
else:
    print("  [!!][1c] 未匹配 bg.add_task, 请手动改")

# 1d) run_experiment 调用加 meta=
old_call="res = await run_experiment(code, run_id, timeout, gen_video)"
new_call="res = await run_experiment(code, run_id, timeout, gen_video, meta={'data_table': data_table})"
if old_call in t:
    t=t.replace(old_call, new_call)
    print("  [1d] _exec 调用加 meta={'data_table': data_table}")
elif "meta={'data_table': data_table}" in t or 'meta={"data_table": data_table}' in t:
    print("  [1d] 调用已传 meta, 跳过")
else:
    print("  [!!][1d] 未匹配 run_experiment 调用, 请手动改")

open(lab,"w",encoding="utf-8",newline="\n").write(t)
check(lab)

# ==================== 2) orchestrator.py ====================
print("\n=== orchestrator.py ===")
backup(orc)
t=open(orc,encoding="utf-8",errors="ignore").read()
old_c="_res = await run_experiment(_code, _run.id, timeout=120, generate_video=True)"
new_c="_res = await run_experiment(_code, _run.id, timeout=120, generate_video=True, meta={'data_table': None})"
if old_c in t:
    t=t.replace(old_c, new_c)
    print("  [2] orchestrator 调用加 meta={'data_table': None}")
elif "meta={'data_table':" in t or 'meta={"data_table":' in t:
    print("  [2] orchestrator 已传 meta, 跳过")
else:
    print("  [!!][2] 未匹配调用, 请手动改")
open(orc,"w",encoding="utf-8",newline="\n").write(t)
check(orc)

print("\n=== 全部完成, 回滚: ===")
print("  Copy-Item <file>.wire_bak <file>")
