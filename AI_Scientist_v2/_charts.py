# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
print("="*70)
print("[1] challenge_cup_pdf.py 里 _charts 函数（图表是怎么进 PDF 的）")
print("="*70)
P = os.path.join(ROOT, r"app\api\v1\challenge_cup_pdf.py")
lines = open(P, encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    if 32 <= i+1 <= 55:  # _charts 函数
        print(f"L{i+1:>3}| {l.rstrip()[:160]}")

print()
print("="*70)
print("[2] 谁产生图表/视频：搜 generate_chart / matplotlib / plot / figure / experiment / simulation")
print("="*70)
for dp, _, fs in os.walk(ROOT):
    if "__pycache__" in dp: continue
    for fn in fs:
        if not fn.endswith(".py"): continue
        p = os.path.join(dp, fn)
        try: txt = open(p, encoding="utf-8", errors="ignore").read()
        except: continue
        if re.search(r"matplotlib|plotly|seaborn|plt\.|savefig|generate_chart|experiment_runner|simulation|实验模拟|图表|chart\.png|/videos/|/charts/", txt, re.I):
            rel = p.replace(ROOT,"")
            for kw in ["matplotlib","plotly","seaborn","savefig","generate_chart","experiment","simulation","图表","chart","video"]:
                hits = [m for m in re.finditer(rf".{{0,30}}{kw}.{{0,80}}", txt, re.I)]
                if hits:
                    print(f"\nFILE: {rel}")
                    for h in hits[:6]: print(f"   ...{h.group()}...")
                    break
