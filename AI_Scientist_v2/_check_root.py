# -*- coding: utf-8 -*-
import os
# 复刻 L629 的逻辑，看 _PROJ_ROOT 到底指到哪
__file__ = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("[验证] _PROJ_ROOT =", _PROJ_ROOT)
print("[验证] 期望       = D:\\111-1\\AI_Scientist_v2\\backend")
print("[验证] 正确?" , _PROJ_ROOT == r"D:\111-1\AI_Scientist_v2\backend")

# 看四个候选目录哪些存在
for sub in ["deliverables","experiments"]:
    for tail in [f"project_1/charts", "project_1", f"1/charts"]:
        d = os.path.join(_PROJ_ROOT, "output", sub, tail)
        print(f"  {'✓' if os.path.isdir(d) else '✗'} {d}")
