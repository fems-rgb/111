# -*- coding: utf-8 -*-
import sqlite3
DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
print("="*70)
print("science_questions 表结构 + 样例")
print("="*70)
cols = [r["name"] for r in c.execute("PRAGMA table_info(science_questions)")]
print("  列:", cols)
row = c.execute("SELECT * FROM science_questions ORDER BY id DESC LIMIT 1").fetchone()
if row:
    d = dict(row)
    for k, v in d.items():
        s = str(v or "")
        print(f"  {k}: ({len(s)}字) {s[:130]}{'...' if len(s)>130 else ''}")
c.close()
