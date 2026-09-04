# -*- coding: utf-8 -*-
"""精确定位前端"资源解析服务"拦截层入口"""
import subprocess
# 只搜前端源码（排除 node_modules / dist / .next）
frontend = r"D:\111-1\AI_Scientist_v2\frontend\src"
if __import__("os").path.isdir(frontend):
    for kw in ["资源解析服务请求失败", "user_doc_url", "user_doc_content", "解析服务", "fileParser", "parseFile", "requestFailed", "resolveResource", "user_doc"]:
        r = subprocess.run(["findstr", "/S", "/N", kw, frontend], capture_output=True, text=True)
        lines = [l.strip() for l in r.stdout.split("\n") if l.strip()
                 and "node_modules" not in l and "\\.next" not in l and "dist" not in l]
        if lines:
            print(f"=== {kw} ({len(lines)} 处) ===")
            print("\n".join(lines[:15]))

# 也搜 backend（排除 output / bak / pycache）
print("\n=== backend 相关 ===")
r = subprocess.run(["findstr", "/S", "/N", "资源解析", r"D:\111-1\AI_Scientist_v2\backend\app"],
                   capture_output=True, text=True)
lines = [l.strip() for l in r.stdout.split("\n") if l.strip()
         and all(x not in l for x in ["bak", "__pycache__", "output"])]
if lines: print("\n".join(lines[:15]))
else: print("(backend/app 无匹配)")
