# -*- coding: utf-8 -*-
"""一键执行：语法检查 -> 应用三处修复 -> 验证"""
import subprocess, sys

print("="*70)
print("Step 1: 语法预检（修改前确认三个文件可编译）")
print("="*70)
files = [
    r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py",
    r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\proposal_addon.py",
    r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py",
]
for f in files:
    try:
        import py_compile
        py_compile.compile(f, doraise=True)
        print(f"  OK: {f.split(chr(92))[-1]}")
    except py_compile.PyCompileError as e:
        print(f"  FAIL: {f}: L{e.lineno}: {e.msg}")

print()
print("="*70)
print("Step 2: 应用三处修复")
print("="*70)
for script in ["_apply_fix1.py", "_apply_fix2.py", "_apply_fix3.py"]:
    print(f"\n--- {script} ---")
    res = subprocess.run([sys.executable, script], capture_output=False)
    if res.returncode != 0:
        print(f"  ⚠️ {script} 返回 {res.returncode}")

print()
print("="*70)
print("Step 3: 最终语法检查")
print("="*70)
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"  OK: {f.split(chr(92))[-1]}")
    except py_compile.PyCompileError as e:
        print(f"  ❌ {f}: L{e.lineno}: {e.msg}")

print()
print("="*70)
print("Step 4: 功能验证（模拟渲染）")
print("="*70)
res = subprocess.run([sys.executable, "_verify_final.py"], capture_output=False)
