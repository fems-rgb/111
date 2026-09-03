# -*- coding: utf-8 -*-
import os, re
# 找"资源解析服务"本身：谁在 fetch 这些 URL、谁维护"待解析列表"
ROOT = r"D:\111-1\AI_Scientist_v2\frontend\src"
kw = ["资源解析", "parseResource", "resourceParser", "ResourceParse", "docParser",
      "解析服务", "parseDoc", "previewUrl", "toPreview", "addToParse", "parseQueue",
      "resume", "DocumentPreview", "useResource"]
for dp, _, fs in os.walk(ROOT):
    if "node_modules" in dp: continue
    for fn in fs:
        if not fn.endswith((".ts",".tsx",".js",".vue")): continue
        p = os.path.join(dp, fn)
        txt = open(p, encoding="utf-8", errors="ignore").read()
        hits = []
        for i, l in enumerate(txt.split("\n")):
            if any(k.lower() in l.lower() for k in kw) and l.strip():
                hits.append(f"  L{i+1:>3}| {l.strip()[:160]}")
        if hits:
            print("="*70)
            print(p.replace(ROOT,""))
            print("="*70)
            for h in hits[:25]: print(h)
