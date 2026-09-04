# -*- coding: utf-8 -*-
"""搜前端：怎么消费 question_tasks.result / report_pdf / fetch-url"""
import os, re
frontend = r"D:\111-1\AI_Scientist_v2\frontend\src"

for dirpath, dirs, files in os.walk(frontend):
    if any(x in dirpath for x in ["node_modules", "dist", ".next", "build"]): continue
    for f in files:
        if not f.endswith((".vue", ".ts", ".js")): continue
        fp = os.path.join(dirpath, f)
        try: t = open(fp, encoding="utf-8", errors="ignore").read()
        except: continue
        for i, l in enumerate(t.split("\n")):
            if re.search(r"report_pdf|result\.|fetch-url|fetchUrl|user_doc|userDoc|资源解析|解析服务|parseStatus|parse_status", l):
                print(f"{os.path.relpath(fp, frontend)}:{i+1}  {l.strip()[:220]}")
