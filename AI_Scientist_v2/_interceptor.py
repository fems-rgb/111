# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\frontend\src"
# 找 axios/client 的响应拦截器 + 错误提示
for dp, _, fs in os.walk(ROOT):
    if "node_modules" in dp: continue
    for fn in fs:
        if not fn.endswith((".ts",".tsx",".js")): continue
        p = os.path.join(dp, fn)
        txt = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        for i, l in enumerate(txt):
            s = l.strip()
            if re.search(r"interceptor|响应拦截|response\.use|请求失败|请求出错|catch|onError|showToast.*error|Message\.error", s):
                if s:
                    print(f"[{p.replace(ROOT,'')} L{i+1}] {s[:170]}")
