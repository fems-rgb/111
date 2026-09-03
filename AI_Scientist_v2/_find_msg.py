# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\frontend\src"
# 找"资源解析服务请求失败"这句文案的来源
for dp, _, fs in os.walk(ROOT):
    if "node_modules" in dp: continue
    for fn in fs:
        if not fn.endswith((".ts",".tsx",".js",".vue")): continue
        p = os.path.join(dp, fn)
        txt = open(p, encoding="utf-8", errors="ignore").read()
        if "资源解析服务" in txt:
            for i, l in enumerate(txt.split("\n")):
                if "资源解析" in l:
                    print(f"[{p.replace(ROOT,'')} L{i+1}] {l.strip()[:180]}")
