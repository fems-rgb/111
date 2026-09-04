# -*- coding: utf-8 -*-
import os, re
# 搜索"资源解析/解析服务/请求失败"相关文案
targets = [
    r"D:\111-1\AI_Scientist_v2\frontend\src",
    r"D:\111-1\AI_Scientist_v2\backend",
]
for ROOT in targets:
    if not os.path.exists(ROOT): continue
    for dp, _, fs in os.walk(ROOT):
        if "node_modules" in dp or "__pycache__" in dp: continue
        for fn in fs:
            if not fn.endswith((".ts",".tsx",".js",".vue",".py",".json",".md")): continue
            p = os.path.join(dp, fn)
            try: t = open(p, encoding="utf-8", errors="ignore").read()
            except: continue
            if "资源解析" in t or "解析服务" in t or ("请求失败" in t and "服务" in t):
                print("FILE:", p.replace(r"D:\111-1\AI_Scientist_v2",""))
                for i, l in enumerate(t.split("\n")):
                    if "资源解析" in l or "解析服务" in l or ("请求失败" in l and "服务" in l):
                        print(f"  L{i+1:>3}| {l.strip()[:200]}")
