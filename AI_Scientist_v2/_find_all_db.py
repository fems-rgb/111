# -*- coding: utf-8 -*-
"""在整个 D 盘搜 zhixing*.db，找到前端真正用的那个"""
import os
hits = []
for root, dirs, files in os.walk("D:\\"):
    if "node_modules" in root or "__pycache__" in root:
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".git")]
        continue
    for fn in files:
        if fn.startswith("zhixing") and fn.endswith(".db"):
            p = os.path.join(root, fn)
            try: hits.append((p, os.path.getsize(p)))
            except: pass
    # 限制深度，避免扫太久
    depth = root.count(os.sep) - 2
    if depth > 6:
        dirs[:] = []
print("=== D 盘所有 zhixing*.db ===")
for p, sz in sorted(hits, key=lambda x: -x[1]):
    print(f"  {p}  ({sz//1024} KB)")
