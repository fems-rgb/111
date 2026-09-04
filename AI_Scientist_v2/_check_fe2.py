# -*- coding: utf-8 -*-
"""看前端如何连后端 + 后端实际用的是哪个 DB 文件"""
import os

# 1. 前端配置（API 地址）
print("=== 前端 API 配置 ===")
for p in [
    r"D:\111-1\AI_Scientist_v2\frontend\.env",
    r"D:\111-1\AI_Scientist_v2\frontend\.env.development",
    r"D:\111-1\AI_Scientist_v2\frontend\vite.config.ts",
    r"D:\111-1\AI_Scientist_v2\frontend\vite.config.js",
]:
    if os.path.exists(p):
        print(f"\n--- {os.path.basename(p)} ---")
        for l in open(p, encoding="utf-8", errors="ignore"):
            if "API" in l or "proxy" in l or "8000" in l or "localhost" in l or "BASE" in l:
                print("  ", l.strip()[:120])

# 2. 后端启动时实际打开的 DB（看进程打开的文件句柄 —— Windows 用 handle 或 wmic）
print("\n=== 提示 ===")
print("请运行：Get-Process python | Select-Object Id")
print("然后：handles.exe -p <PID> | Select-String zhixing")
print("（需要 Sysinternals handle.exe）")
