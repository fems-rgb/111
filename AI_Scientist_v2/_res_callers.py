# -*- coding: utf-8 -*-
import re
ROOT = r"D:\111-1\AI_Scientist_v2\frontend\src"
# 1. resume 的调用方 + 2. tasks/${id} 的调用方
targets = {
    "/projects/${id}/resume": None,
    "/questions/tasks/${taskId}": None,
}
for dp, _, fs in os.walk(ROOT):
    if "node_modules" in dp: continue
    for fn in fs:
        if not fn.endswith((".ts",".tsx",".js",".vue")): continue
        p = os.path.join(dp, fn)
        txt = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(txt):
            for key in targets:
                if key in l:
                    print(f"[{p.replace(ROOT,'')} L{i+1}] {l.strip()[:150]}")
