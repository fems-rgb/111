# -*- coding: utf-8 -*-
"""搜前端：API 调用 + 错误处理 + user_doc 相关"""
import subprocess, os
frontend = r"D:\111-1\AI_Scientist_v2\frontend\src"

# 搜 axios 调用、错误提示、文档相关
for kw in ["资源解析", "解析服务", "requestFailed", "user_doc", "userDoc", "parseDocument", "解析文档", 
           "Message.error", "ElMessage", "notify", "catch", "/api/", "axios.post", "axios.get"]:
    r = subprocess.run(["findstr", "/S", "/N", kw, frontend], capture_output=True, text=True)
    lines = [l.strip() for l in r.stdout.split("\n") if l.strip()
             and all(x not in l for x in ["node_modules", "dist", ".next"])]
    if lines:
        print(f"=== {kw} ({len(lines)} 处) ===")
        print("\n".join(lines[:12]))
