# -*- coding: utf-8 -*-
import os, re
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
print("[3] 图表/视频存放目录现状（看有没有实时产出的图）")
for base in [r"output", r"static", r"app\static", r"output\charts", r"output\videos", r"output\figures"]:
    d = os.path.join(ROOT, base)
    if os.path.exists(d):
        print(f"\n{d}  (存在)")
        for root, dirs, files in os.walk(d):
            if any(x in root for x in ("__pycache__",)): continue
            for f in sorted(files)[:12]:
                if f.lower().endswith((".png",".jpg",".svg",".mp4",".gif",".webm")):
                    fp = os.path.join(root, f)
                    print(f"   {os.path.relpath(fp, d)}  ({os.path.getsize(fp)//1024}KB, {os.path.getmtime(fp):.0f})")
print()
print("[4] 数据库里图表/视频字段（project 表有哪些图相关列）")
import sqlite3
for db in [r"D:\111-1\AI_Scientist_v2\zhixing.db",
           os.path.join(ROOT, r"app\data.db"),
           os.path.join(ROOT, r"instance\app.db")]:
    if os.path.exists(db):
        print(f"\nDB: {db}")
        try:
            c = sqlite3.connect(db); c.row_factory = sqlite3.Row
            for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if "project" in name.lower():
                    cols = [r[1] for r in c.execute(f"PRAGMA table_info({name})")]
                    imgcols = [col for col in cols if re.search(r"chart|figure|image|video|plot|graph|diagram|media|fig_|img_", col, re.I)]
                    print(f"  {name}: {len(cols)} 列  -> 图相关: {imgcols if imgcols else '无'}")
            c.close()
        except Exception as e:
            print("  err", e)
