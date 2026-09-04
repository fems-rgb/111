# -*- coding: utf-8 -*-
"""精准：在 stageC 的 if _charts 块之后，插入『先清空 + 同步』逻辑（正则定位）"""
import shutil, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
shutil.copy(P, P + ".bak_sync2")
src = open(P, encoding="utf-8").read()

# 定位：if _charts: 块结束处（L365 await db.commit() 之后，L366 logger.info 之前）
# 匹配从 "if _charts:" 到下一个同级语句（logger.info("[stageC] 模拟场完成"）之间的整段
pattern = re.compile(
    r'(\s*)if _charts:\s*\n'
    r'(.*?)(?=\s*logger\.info\("\[stageC\] 模拟场完成)',
    re.S
)

m = pattern.search(src)
assert m, "if _charts 块未匹配，打印 stageC 全文"
indent = m.group(1)  # 块内缩进

SYNC = '''\
{indent}                                    # [sync] 清空 + 把本次实验图同步到 deliverables/project_{{project_id}}/charts/
{indent}                                    try:
{indent}                                        import os as _os, shutil as _sh, glob as _glb
{indent}                                        _exp_charts = _os.path.join(OUTPUT_ROOT, str(_run.id), "charts")
{indent}                                        _backend = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
{indent}                                        _deli_charts = _os.path.join(_backend, "output", "deliverables", f"project_{{project_id}}", "charts")
{indent}                                        if _os.path.isdir(_exp_charts):
{indent}                                            _os.makedirs(_deli_charts, exist_ok=True)
{indent}                                            # 清空旧图（避免占位图/历史图残留）
{indent}                                            for _old in _glb.glob(_os.path.join(_deli_charts, "*")):
{indent}                                                try: _os.remove(_old)
{indent}                                                except Exception: pass
{indent}                                            for _fn in sorted(_os.listdir(_exp_charts)):
{indent}                                                if _fn.lower().endswith((".png",".jpg",".jpeg",".svg")):
{indent}                                                    _sh.copy(_os.path.join(_exp_charts, _fn),
{indent}                                                             _os.path.join(_deli_charts, _fn))
{indent}                                            logger.info("[stageC] 同步图到 %s: %s", _deli_charts, sorted(_os.listdir(_deli_charts)))
{indent}                                    except Exception as _se:
{indent}                                        logger.warning("[stageC] 同步图失败（不阻塞）: %s", _se)
{indent}
'''.format(indent=indent)

new_block = m.group(0) + SYNC
src = src[:m.start()] + new_block + src[m.end():]
open(P, "w", encoding="utf-8").write(src)
print("[已修改] stageC: if _charts 块后插入清空+同步逻辑")

import py_compile
try: py_compile.compile(P, doraise=True); print("[语法OK]")
except Exception as e: print("[语法错误]", e)

# 打印 L353-385 确认
lines = open(P, encoding="utf-8").read().split("\n")
print("\n=== 插入后 L353-390 ===")
for i in range(352, 390):
    print(f"L{i+1:>3}| {lines[i].rstrip()[:170]}")
