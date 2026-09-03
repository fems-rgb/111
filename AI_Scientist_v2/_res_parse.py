# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\frontend\src"
for dp, _, fs in os.walk(ROOT):
    if "node_modules" in dp: continue
    for fn in fs:
        if fn.endswith((".ts",".tsx",".js",".vue")):
            p = os.path.join(dp, fn)
            txt = open(p, encoding="utf-8", errors="ignore").read()
            if "/resume" in txt or "questions/tasks" in txt or "资源解析" in txt:
                print("FILE:", p.replace(ROOT,""))
                for m in re.finditer(r".{0,40}(/resume|questions/tasks|资源解析|parseResource|resourceParser|DocumentPreview|docPreview).{0,60}", txt, re.I):
                    print(f"   ...{m.group()}...")
