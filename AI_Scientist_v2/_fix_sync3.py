# -*- coding: utf-8 -*-
"""从 .bak_sync2 恢复 orchestrator.py 到插入前状态，再用正确缩进重新插入"""
import shutil, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
BAK = P + ".bak_sync2"
src = open(BAK, encoding="utf-8").read()  # 用备份（插入前的干净版本）

# 定位 if _charts: 块结束处（在 "logger.info("[stageC] 模拟场完成" 之前）
pattern = re.compile(
    r'(\s*)if _charts:\s*\n'
    r'(.*?)(?=\s*logger\.info\("\[stageC\] 模拟场完成)',
    re.S
)
m = pattern.search(src)
assert m, "if _charts 块未匹配"
base_indent = m.group(1)  # 例如 "                                    " (L353 的缩进)

# SYNC 块的缩进：与 if _charts: 块内同级（即 base_indent + 一级）
# 观察原代码：L354 _pr = ... 比 L353 if _charts: 多 4 空格
inner = base_indent + "    "  # 块内一级缩进
SYNC = (
    f"{base_indent}                                    "
    "# [sync] 清空 + 把本次实验图同步到 deliverables/project_{{project_id}}/charts/\n"
    f"{inner}try:\n"
    f"{inner}    import os as _os, shutil as _sh, glob as _glb\n"
    f"{inner}    _exp_charts = _os.path.join(OUTPUT_ROOT, str(_run.id), 'charts')\n"
    f"{inner}    _backend = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))\n"
    f"{inner}    _deli_charts = _os.path.join(_backend, 'output', 'deliverables', f'project_{{project_id}}', 'charts')\n"
    f"{inner}    if _os.path.isdir(_exp_charts):\n"
    f"{inner}        _os.makedirs(_deli_charts, exist_ok=True)\n"
    f"{inner}        for _old in _glb.glob(_os.path.join(_deli_charts, '*')):\n"
    f"{inner}            try: _os.remove(_old)\n"
    f"{inner}            except Exception: pass\n"
    f"{inner}        for _fn in sorted(_os.listdir(_exp_charts)):\n"
    f"{inner}            if _fn.lower().endswith(('.png','.jpg','.jpeg','.svg')):\n"
    f"{inner}                _sh.copy(_os.path.join(_exp_charts, _fn),\n"
    f"{inner}                         _os.path.join(_deli_charts, _fn))\n"
    f"{inner}        logger.info('[stageC] 同步图到 %s: %s', _deli_charts, sorted(_os.listdir(_deli_charts)))\n"
    f"{inner}except Exception as _se:\n"
    f"{inner}    logger.warning('[stageC] 同步图失败（不阻塞）: %s', _se)\n"
)

new_block = m.group(0) + SYNC
src = src[:m.start()] + new_block + src[m.end():]
open(P, "w", encoding="utf-8").write(src)
print("[已修改] stageC: 插入清空+同步逻辑（正确缩进）")

import py_compile
try: py_compile.compile(P, doraise=True); print("[语法OK]")
except Exception as e: print("[语法错误]", e)

# 打印 L353-390 确认缩进
lines = open(P, encoding="utf-8").read().split("\n")
print("\n=== 插入后 L353-392 ===")
for i in range(352, 392):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:150]}")
