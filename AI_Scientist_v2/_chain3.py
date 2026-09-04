# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
print("=== [Y1] experiment_plan 的输出（有没有 python 代码块）===")
import sqlite3
# 找数据库
for db in [r"D:\111-1\AI_Scientist_v2\zhixing.db",
           os.path.join(ROOT, "app", "data.db"),
           os.path.join(ROOT, "instance", "app.db")]:
    if os.path.exists(db):
        print(f"\nDB: {db}")
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row
        tables = [n for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print("tables:", tables)
        c.close()

print("\n=== [Y2] orchestrator 里 _extract_experiment_code 逻辑 ===")
P = os.path.join(ROOT, r"app\agents\orchestrator.py")
txt = open(P, encoding="utf-8").read().split("\n")
for i, l in enumerate(txt):
    if 15 <= i+1 <= 70:  # _extract_experiment_code 函数
        print(f"L{i+1:>3}| {l.rstrip()[:160]}")

print("\n=== [Y3] writing.py 是否生成可视化代码 ===")
P2 = os.path.join(ROOT, r"app\agents\writing.py")
t2 = open(P2, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(t2):
    s = l.strip()
    if re.search(r"图表|可视化|visualization|plot|matplotlib|figure|fig_|chart|实验图|生成图", s, re.I) and s:
        print(f"L{i+1:>3}| {s[:160]}")
