# -*- coding: utf-8 -*-
# 2. 前端导出按钮 + API 调用（确认手动导出链路）
import re
for p in [r"D:\111-1\AI_Scientist_v2\frontend\src\utils\exportPaper.js",
          r"D:\111-1\AI_Scientist_v2\frontend\src\views\workspace\ProjectDetail.vue"]:
    print("="*70)
    print(p)
    print("="*70)
    txt = open(p, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r".{0,50}(导出|exportPaper|download|challenge.*pdf|/api/.*pdf|generatePdf|axios.*pdf|fetch.*pdf).{0,80}", txt, re.I):
        print(f"   ...{m.group()}...")
