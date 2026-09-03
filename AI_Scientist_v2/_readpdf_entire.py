# -*- coding: utf-8 -*-
"""读 challenge_cup_pdf.py 全文关键行：入口、project 来源、ctx 组装"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py"
lines = open(p, encoding="utf-8").read().split("\n")
print("总行数:", len(lines))
for i, l in enumerate(lines):
    s = l.rstrip()
    if any(k in s for k in ["import ","from ","def ","project =","project=","get_project","db.query","Project)","first()","ctx =","_latex","rationale","methods","experiments","hypotheses","paper_","abstract","final_output","metadata","writing","generate_challenge"]):
        print("%4d| %s" % (i+1, s[:150]))
