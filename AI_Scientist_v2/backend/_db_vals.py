# -*- coding: utf-8 -*-
"""直接查 DB 里 agent_tasks.status 的所有实际值"""
import sqlite3
DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
print("=== agent_tasks.status 实际值 ===")
cur.execute("SELECT DISTINCT status FROM agent_tasks")
for (v,) in cur.fetchall():
    print(f"  {v!r}")
conn.close()
