# -*- coding: utf-8 -*-
"""查 export.py / proposal_addon.py 里技术栈表「用途」列是否还有硬编码"""
import glob
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
for pat in ["**/*.py"]:
    for path in glob.glob(f"{ROOT}/{pat}", recursive=True):
        try: src = open(path, encoding="utf-8").read()
        except: continue
        for kw in ["功率谱拟合","宇宙网建模","CMB 图像","CMB图像","GNN","emcee","技术栈","用途.*CMB","CMB.*用途"]:
            if kw in src.replace("\n"," "):
                ls = src.split("\n")
                for i, l in enumerate(ls):
                    if kw.replace(".*","") in l:
                        print(f"{path.split(chr(92))[-1]}:L{i+1}| {l.rstrip()[:150]}")
