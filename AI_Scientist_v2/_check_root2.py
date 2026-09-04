# -*- coding: utf-8 -*-
"""只做一件事：确认 export.py 里 _PROJ_ROOT 现在指向 backend"""
import os
# 直接复刻 export.py L629 的计算
__file__ = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print("[验证] _PROJ_ROOT =", _PROJ_ROOT)
print("[验证] 期望       = D:\\111-1\\AI_Scientist_v2\\backend")
print("[验证] 正确?" , _PROJ_ROOT == r"D:\111-1\AI_Scientist_v2\backend")
print()

# 看四个候选目录哪些存在
for sub in ["deliverables","experiments"]:
    for tail in ["project_1/charts", "project_1", "1/charts"]:
        d = os.path.join(_PROJ_ROOT, "output", sub, tail)
        print(f"  {'✓' if os.path.isdir(d) else '✗'} {d}")
