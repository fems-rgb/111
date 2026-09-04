# -*- coding: utf-8 -*-
"""全仓搜：资源解析 / user_doc / 文档解析 - 在 backend 全范围"""
import subprocess, os
for kw in ["资源解析", "user_doc", "解析服务", "fileParser", "parseFile", "resolveResource", "文档解析", "requestFailed", "doc_url", "doc_content"]:
    # backend 全范围（排除 output/bak/pycache）
    r = subprocess.run(["findstr", "/S", "/N", kw, r"D:\111-1\AI_Scientist_v2\backend"],
                        capture_output=True, text=True)
    lines = [l.strip() for l in r.stdout.split("\n") if l.strip()
             and all(x not in l for x in ["bak", "__pycache__", "output", ".bak2", ".bak_"])]
    if lines:
        print(f"=== backend | {kw} ({len(lines)} 处) ===")
        print("\n".join(lines[:20]))

# 也看 frontend 的 package.json 依赖（是否用了第三方解析 SDK）
print("\n=== frontend 依赖（可能调用外部解析 API）===")
pkg = r"D:\111-1\AI_Scientist_v2\frontend\package.json"
if os.path.exists(pkg):
    print(open(pkg, encoding="utf-8").read()[:2000])
