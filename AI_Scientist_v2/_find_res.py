# -*- coding: utf-8 -*-
"""定位前端"资源解析服务"拦截层入口（所有 URL 都被它无差别拦截）"""
import subprocess
for kw in ["资源解析服务请求失败", "user_doc_url", "file_parser", "parseResource", "资源解析"]:
    r = subprocess.run(["findstr", "/S", "/N", kw, r"D:\111-1\AI_Scientist_v2\frontend\src"],
                        capture_output=True, text=True)
    if r.stdout:
        print(f"=== 关键词: {kw} ===")
        print(r.stdout[:1500])
