# -*- coding: utf-8 -*-
import re
for p in [r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py",
          r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\proposal_addon.py",
          r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py"]:
    print("="*70)
    print(p.split("AI_Scientist_v2")[-1])
    print("="*70)
    txt = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(txt):
        s = l.rstrip()
        if re.search(r"generate_challenge_cup_pdf|_gen_pdf|case_pdf|pdf_path|export", s, re.I) and s.strip():
            print(f"  L{i+1:>3}| {s[:150]}")
