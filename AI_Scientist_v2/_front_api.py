# -*- coding: utf-8 -*-
import re
p = r"D:\111-1\AI_Scientist_v2\frontend\src\views\workspace\ProjectDetail.vue"
txt = open(p, encoding="utf-8", errors="ignore").read()
# 找所有 API 调用（axios/fetch/$http/api）和导出相关方法
for i, l in enumerate(txt.split("\n")):
    s = l.strip()
    if re.search(r"axios|fetch\(|\$http|\.get\(|\.post\(|api\.", s) or re.search(r"export|pdf|download|导出", s, re.I) and ("=>" in s or "function" in s or s.startswith("async") or s.startswith("const")):
        if s:
            print(f"L{i+1:>3}| {s[:160]}")
