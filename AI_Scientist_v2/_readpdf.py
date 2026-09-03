# -*- coding: utf-8 -*-
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\challenge_cup_pdf.py"
lines = open(p, encoding="utf-8").read().split("\n")
print("="*64)
print("challenge_cup_pdf.py : weasyprint / CSS / render 相关")
print("="*64)
for i, l in enumerate(lines):
    s = l.rstrip()
    if any(k in s for k in ["weasyprint", "Weasy", "from_string", "HTML(", "render", "css", "CSS(", "template", "style", "@page", "base_url"]):
        print("%4d| %s" % (i+1, s[:140]))
