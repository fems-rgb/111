# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"

print("=== [X1] orchestrator stageC：ExperimentRun.charts 是否回写 ===")
P = os.path.join(ROOT, r"app\agents\orchestrator.py")
txt = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(txt):
    s = l.strip()
    if re.search(r"stageC|run_experiment|ExperimentRun|charts|\.charts|experiment_plan", s) and s:
        print(f"  L{i+1:>3}| {s[:170]}")

print("\n=== [X2] ExperimentRun 模型：charts 字段定义 ===")
for dp, _, fs in os.walk(os.path.join(ROOT, "app")):
    if "__pycache__" in dp: continue
    for fn in fs:
        if fn in ("models.py",) or fn.endswith("_models.py"):
            p = os.path.join(dp, fn)
            t = open(p, encoding="utf-8", errors="ignore").read()
            if "ExperimentRun" in t:
                print(f"\nFILE: {p.replace(ROOT,'')}")
                in_cls = False
                for i, l in enumerate(t.split("\n")):
                    if "class ExperimentRun" in l: in_cls = True
                    if in_cls:
                        print(f"  L{i+1:>3}| {l.strip()[:150]}")
                        if l.strip().startswith("class ") and "ExperimentRun" not in l: break
                        if re.search(r"charts|class Meta|__tablename__", l) and i>0: 
                            if "ExperimentRun" not in l: break

print("\n=== [X3] 真实图到底在哪（逐目录统计 png）===")
out = os.path.join(ROOT, "output")
for sub in ["deliverables","experiments"]:
    d = os.path.join(out, sub)
    if not os.path.exists(d): continue
    print(f"\n{d}:")
    cnt=0
    for root, dirs, files in os.walk(d):
        if any(x in root for x in ("__pycache__",)): continue
        pngs = [f for f in files if f.endswith(".png")]
        if pngs and cnt<20:
            for f in sorted(pngs)[:4]:
                fp=os.path.join(root,f)
                print(f"   {os.path.relpath(fp,d)}  ({os.path.getsize(fp)//1024}KB)")
            cnt+=1
    print(f"   ... 共 {sum(1 for _,_,fs in os.walk(d) for f in fs if f.endswith('.png'))} 个 png")
