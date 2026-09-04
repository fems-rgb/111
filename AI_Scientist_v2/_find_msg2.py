# -*- coding: utf-8 -*-
import os, re
# 在后端找"资源解析服务请求失败"这句文案的源头
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
for dp, _, fs in os.walk(ROOT):
    if "__pycache__" in dp: continue
    for fn in fs:
        if not fn.endswith(".py"): continue
        p = os.path.join(dp, fn)
        try: t = open(p, encoding="utf-8", errors="ignore").read()
        except: continue
        if "资源解析" in t:
            print("FILE:", p.replace(ROOT,""))
            for i, l in enumerate(t.split("\n")):
                if "资源解析" in l:
                    print(f"  L{i+1:>3}| {l.strip()[:180]}")
