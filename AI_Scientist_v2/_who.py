# -*- coding: utf-8 -*-
"""查清：机器上跑着几个 python 后端，各用哪个目录的代码"""
import subprocess, os
print("=== 当前所有 python 进程 ===")
r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True)
print(r.stdout or "(无 python.exe 进程)")

print("\n=== 提示：在 PowerShell 管理员窗口跑下面两条 ===")
print("  1) Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { $_.OwningProcess } | Select-Object -Unique")
print("  2) 对每个 PID: Get-Process -Id <PID> | Select-Object Id, Path")
print("\n=== 当前工作目录 ===")
print("  cwd:", os.getcwd())
