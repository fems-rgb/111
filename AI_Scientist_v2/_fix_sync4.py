# -*- coding: utf-8 -*-
"""从 .bak_sync2（干净版）恢复，用 textwrap 精确控制缩进重插同步逻辑"""
import shutil, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
BAK = P + ".bak_sync2"   # 这是插入前的干净版本
src = open(BAK, encoding="utf-8").read()

# 定位 "if _charts:" 块（到 "logger.info("[stageC] 模拟场完成" 之前）
pattern = re.compile(
    r'(\s*)if _charts:\s*\n'
    r'(.*?)(?=\s*logger\.info\("\[stageC\] 模拟场完成)',
    re.S
)
m = pattern.search(src)
assert m, "if _charts 块未匹配"
base_indent = m.group(1)   # L353 的缩进（36 空格）
inner = base_indent + "    "  # 块内一级（40 空格）

# 同步逻辑（用 inner 作为基础缩进，每行缩进明确）
SYNC_LINES = [
    f"{inner}# [sync] 清空 + 同步实验图到 deliverables/project_{{project_id}}/charts/",
    f"{inner}try:",
    f"{inner}    import os as _os, shutil as _sh, glob as _glb",
    f"{inner}    _exp_charts = _os.path.join(OUTPUT_ROOT, str(_run.id), 'charts')",
    f"{inner}    _backend = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))",
    f"{inner}    _deli_charts = _os.path.join(_backend, 'output', 'deliverables', f'project_{{project_id}}', 'charts')",
    f"{inner}    if _os.path.isdir(_exp_charts):",
    f"{inner}        _os.makedirs(_deli_charts, exist_ok=True)",
    f"{inner}        for _old in _glb.glob(_os.path.join(_deli_charts, '*')):",
    f"{inner}            try: _os.remove(_old)",
    f"{inner}            except Exception: pass",
    f"{inner}        for _fn in sorted(_os.listdir(_exp_charts)):",
    f"{inner}            if _fn.lower().endswith(('.png','.jpg','.jpeg','.svg')):",
    f"{inner}                _sh.copy(_os.path.join(_exp_charts, _fn),",
    f"{inner}                         _os.path.join(_deli_charts, _fn))",
    f"{inner}        logger.info('[stageC] 同步图到 %s: %s', _deli_charts, sorted(_os.listdir(_deli_charts)))",
    f"{inner}except Exception as _se:",
    f"{inner}    logger.warning('[stageC] 同步图失败（不阻塞）: %s', _se)",
    "",  # 尾部空行
]
SYNC = "\n".join(SYNC_LINES)

new_block = m.group(0) + SYNC
src = src[:m.start()] + new_block + src[m.end():]
open(P, "w", encoding="utf-8").write(src)
print("[已修改] stageC: 用精确缩进重插同步逻辑")

import py_compile
try: py_compile.compile(P, doraise=True); print("[语法OK]")
except Exception as e: print("[语法错误]", e)

# 打印 L353-392 确认缩进层级干净
lines = open(P, encoding="utf-8").read().split("\n")
print("\n=== L353-392（前导空格数）===")
for i in range(352, 392):
    l = lines[i]
    stripped = l.lstrip()
    sp = len(l) - len(stripped)
    print(f"L{i+1:>3}| (sp={sp:>2}) {stripped[:130]}")
