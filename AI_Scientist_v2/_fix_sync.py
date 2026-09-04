# -*- coding: utf-8 -*-
"""治本补充：orchestrator stageC 执行完后，把图同步到 deliverables/project_{pid}/charts/"""
import shutil, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
shutil.copy(P, P + ".bak_sync")
src = open(P, encoding="utf-8").read()

# 在 _auto_generate_charts 调用之后（L353 附近 "if _charts:" 块结束处）插入同步逻辑
OLD = """            for _c in _charts:
                _set(_c, "path", _c.get("path") or _c.get("filename"))
                _run.charts = json.dumps(_charts, ensure_ascii=False)"""

NEW = """            for _c in _charts:
                _set(_c, "path", _c.get("path") or _c.get("filename"))
                _run.charts = json.dumps(_charts, ensure_ascii=False)
            # [sync] 把实验图同步到 deliverables/project_{project_id}/charts/，供 PDF 取用
            try:
                import os as _os, shutil as _sh
                _exp_charts = _os.path.join(OUTPUT_ROOT, str(_run.id), "charts")
                _deli_charts = _os.path.join(
                    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
                    "output", "deliverables", f"project_{project_id}", "charts")
                if _os.path.isdir(_exp_charts):
                    _os.makedirs(_deli_charts, exist_ok=True)
                    for _fn in _os.listdir(_exp_charts):
                        if _fn.lower().endswith((".png",".jpg",".jpeg",".svg")):
                            _sh.copy(_os.path.join(_exp_charts, _fn),
                                     _os.path.join(_deli_charts, _fn))
                    logger.info("[stageC] 同步图到 %s: %s", _deli_charts, _os.listdir(_deli_charts))
            except Exception as _se:
                logger.warning("[stageC] 同步图失败（不阻塞）: %s", _se)"""

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    open(P, "w", encoding="utf-8").write(src)
    print("[已修改] stageC: 执行后同步图到 deliverables/project_{pid}/charts/")
else:
    print("[未匹配] 打印实际行供比对：")
    lines = src.split("\n")
    for i, l in enumerate(lines):
        if 348 <= i+1 <= 360:
            print(f"  L{i+1}| {l}")

import py_compile
try: py_compile.compile(P, doraise=True); print("[语法OK]")
except Exception as e: print("[语法错误]", e)
