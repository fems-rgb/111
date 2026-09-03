# -*- coding: utf-8 -*-
import os, re
# 1. 找谁调用了 generate_challenge_cup_pdf（自动产出的钩子）
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
print("=== 谁调用了 generate_challenge_cup_pdf / challenge_cup_pdf ===")
for dirpath, _, files in os.walk(ROOT):
    if "__pycache__" in dirpath: continue
    for fn in files:
        if fn.endswith(".py"):
            p = os.path.join(dirpath, fn)
            txt = open(p, encoding="utf-8", errors="ignore").read()
            if re.search(r"generate_challenge_cup_pdf|challenge_cup_pdf\.generate|from .*challenge_cup_pdf|import.*challenge_cup_pdf", txt):
                for m in re.finditer(r".{0,60}(generate_challenge_cup_pdf|challenge_cup_pdf\.generate).{0,60}", txt):
                    print(f"  {p.replace(ROOT,'' )}: ...{m.group()}...")
