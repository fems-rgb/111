# -*- coding: utf-8 -*-
"""修复 export.py：_PROJ_ROOT 改为 dirname×4，指向 backend"""
import shutil, os
P = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
shutil.copy(P, P + ".bak_root")
lines = open(P, encoding="utf-8").read().split("\n")

# L629：dirname×3 → dirname×4
OLD = """        _PROJ_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))"""
NEW = """        _PROJ_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))"""

assert OLD in "\n".join(lines), "L629 未匹配，打印实际行"
src = "\n".join(lines).replace(OLD, NEW, 1)
open(P, "w", encoding="utf-8").write(src)
print("[已修改] _PROJ_ROOT: dirname×3 → dirname×4")

# 验证
ns = {}
exec(compile(open(P, encoding="utf-8").read(), P, "exec").replace("logger", "ns_logger"), ns)
# 直接复刻计算
__file__ = P
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print("[验证] _PROJ_ROOT =", _PROJ_ROOT)
print("[验证] 正确?" , _PROJ_ROOT == r"D:\111-1\AI_Scientist_v2\backend")

# 看候选目录
for sub in ["deliverables","experiments"]:
    for tail in [f"project_1/charts", "project_1", f"1/charts"]:
        d = os.path.join(_PROJ_ROOT, "output", sub, tail)
        print(f"  {'✓' if os.path.isdir(d) else '✗'} {d}")
