# -*- coding: utf-8 -*-
"""修：experiment_engine.py OUTPUT_ROOT 改为基于文件位置的绝对路径"""
import shutil
P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
shutil.copy(P, P + ".bak_outputroot")
lines = open(P, encoding="utf-8").read().split("\n")

OLD = "OUTPUT_ROOT = os.path.join(os.getcwd(), 'output', 'experiments')"
NEW = """# [fix] 基于本文件位置计算 backend 根目录，避免依赖启动 cwd
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_ROOT = os.path.join(_BACKEND_ROOT, 'output', 'experiments')"""

assert any(OLD == l.strip() for l in lines), "L6 未匹配，打印实际行"
for i, l in enumerate(lines):
    if l.strip() == OLD:
        indent = l[:len(l)-len(l.lstrip())]
        lines[i] = indent + NEW
        break
open(P, "w", encoding="utf-8").write("\n".join(lines))
print("[已修改] OUTPUT_ROOT: os.getcwd() → 基于 __file__ 的绝对路径")

import py_compile
try: py_compile.compile(P, doraise=True); print("[语法OK]")
except Exception as e: print("[语法错误]", e)

# 验证 OUTPUT_ROOT 现在正确
import importlib.util
spec = importlib.util.spec_from_file_location("ee", P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("[验证] OUTPUT_ROOT =", mod.OUTPUT_ROOT)
print("[验证] 正确?", mod.OUTPUT_ROOT == r"D:\111-1\AI_Scientist_v2\backend\output\experiments")
