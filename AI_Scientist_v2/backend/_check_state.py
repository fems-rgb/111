# -*- coding: utf-8 -*-
"""确认 orchestrator/orchestrator 备份一致 + experiment_engine 是原始状态"""
import os
P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
BAK = P + ".bak_chart"
print("experiment_engine.py 行数:", len(open(P, encoding="utf-8", errors="ignore").read().split("\n")))
print("bak_chart 存在:", os.path.exists(BAK))
# 若想确认内容一致（可选）:
print("engine 含旧假图代码(np.random.rand(60)):", "np.random.rand(60)" in open(P, encoding="utf-8", errors="ignore").read())
