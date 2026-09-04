# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"

print("="*70)
print("[A] experiment_engine.py 产出图后存到哪（OUTPUT_ROOT / charts 目录）")
print("="*70)
P = os.path.join(ROOT, r"app\services\experiment_engine.py")
txt = open(P, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(txt):
    s = l.strip()
    if re.search(r"OUTPUT_ROOT|savefig|charts|output_dir|mkdir|write|fig\.|/videos/|/charts/|\.png|\.mp4", s, re.I):
        print(f"  L{i+1:>3}| {s[:150]}")

print()
print("="*70)
print("[B] export.py 的「三源合并」取图逻辑（PDF 实际怎么拿图的）")
print("="*70)
P2 = os.path.join(ROOT, r"app\api\v1\export.py")
txt2 = open(P2, encoding="utf-8", errors="ignore").read().split("\n")
in_block = False
for i, l in enumerate(txt2):
    s = l.strip()
    if "三源合并" in l or "charts" in l.lower():
        in_block = True
    if in_block:
        print(f"  L{i+1:>3}| {s[:160]}")
        if re.search(r"return|# ===|# ---", l) and i > 1050:  # 粗略：到了函数结尾
            in_block = False
    if re.search(r"def .*chart|def .*figure|def .*media|def build.*html|charts.*=|all_charts", s):
        print(f"  >>> {s[:150]}")

print()
print("="*70)
print("[C] ExperimentRun 表结构 + 是否存了 charts")
print("="*70)
import sqlite3
for db in [r"D:\111-1\AI_Scientist_v2\zhixing.db"]:
    if os.path.exists(db):
        c = sqlite3.connect(db); c.row_factory = sqlite3.Row
        tables = [n for (n,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print("tables:", [t for t in tables if "experiment" in t.lower() or "project" in t.lower()])
        for t in tables:
            if "experiment" in t.lower():
                cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})")]
                print(f"  {t}: {cols}")
                # 看有没有 charts 数据
                try:
                    row = c.execute(f"SELECT * FROM {t} LIMIT 1").fetchone()
                    if row:
                        print("     sample:", {k: (str(v)[:60]) for k,v in row.items()})
                except Exception as e:
                    print("     err", e)
        c.close()
