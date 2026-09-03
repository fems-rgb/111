# -*- coding: utf-8 -*-
"""找 generate_challenge_cup_pdf 的调用方"""
import glob, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
for pat in ["**/*.py"]:
    for path in glob.glob(f"{ROOT}/{pat}", recursive=True):
        try: src = open(path, encoding="utf-8").read()
        except: continue
        if "generate_challenge_cup_pdf" in src and "def generate_challenge_cup_pdf" not in src:
            print("="*70)
            print(path.replace(ROOT+"\\",""))
            print("="*70)
            for i, l in enumerate(src.split("\n")):
                if "generate_challenge_cup_pdf" in l or "research_question" in l or "project =" in l or "Project(" in l or "project_id" in l:
                    print(f"  L{i+1}| {l.rstrip()[:160]}")
