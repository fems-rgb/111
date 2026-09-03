# -*- coding: utf-8 -*-
"""确认各表数据量，并列出所有"领域相关"fallback 默认值"""
import sqlite3

DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row

print("="*70)
print("[1] 各表行数")
print("="*70)
for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    t = r["name"]
    try:
        n = c.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
        if n > 0:
            print(f"  {t}: {n} 行")
    except Exception:
        pass

print()
print("="*70)
print("[2] projects 表是否有任何数据")
print("="*70)
n = c.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"]
print(f"  projects: {n} 行")
if n > 0:
    for r in c.execute("SELECT id, title, research_question FROM projects ORDER BY id DESC LIMIT 3"):
        print(f"    id={r['id']} title={str(r['title'])[:50]} rq={str(r['research_question'])[:50]}")
else:
    print("  ⚠️ projects 表为空 —— 这就是 PDF 内容走 fallback 的原因！")

c.close()
