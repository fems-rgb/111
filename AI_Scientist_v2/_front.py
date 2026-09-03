# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2"
hits = []
for dirpath, _, files in os.walk(ROOT):
    if any(x in dirpath for x in ("node_modules","__pycache__",".git","dist","build",".next")):
        continue
    for fn in files:
        if fn.endswith((".tsx",".ts",".jsx",".js",".vue")):
            p = os.path.join(dirpath, fn)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if re.search(r"导出|exportPdf|downloadPdf|challenge.*pdf|generatePdf|pdf.*export", txt, re.I):
                hits.append((p, [m for m in re.findall(r".{0,40}(导出|exportPdf|downloadPdf|generatePdf|challenge.*pdf|导出PDF|exportPDF).{0,40}", txt, re.I)][:3]))
for p, ms in hits:
    print("FILE:", p)
    for m in ms:
        print("   ...", m)
