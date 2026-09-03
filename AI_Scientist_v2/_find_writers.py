# -*- coding: utf-8 -*-
"""找 agent/服务里往 project 领域字段写入的逻辑，定位为何会写入宇宙学占位符"""
import glob, re

ROOT = r"D:\111-1\AI_Scientist_v2\backend"
keywords = ["rationale", "paper_title", "methods", "experiments", "hypotheses",
            "project.methods", "project.experiments", "WIMP", "暗物质", "CMB", "Planck", "SDSS",
            ".methods =", ".experiments =", ".rationale ="]

for pat in ["**/*.py"]:
    for path in glob.glob(f"{ROOT}/{pat}", recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                src = f.read()
        except Exception:
            continue
        hits = [(i+1, l.rstrip()[:130]) for i, l in enumerate(src.split("\n"))
                if any(k in l for k in keywords)]
        if hits:
            print("="*70)
            print(path.replace(ROOT + "\\", ""))
            print("="*70)
            for ln, l in hits[:25]:
                print(f"  L{ln}| {l}")
