# -*- coding: utf-8 -*-
"""确认 DB 里 status 值是否统一（String 模式下大小写敏感）"""
import sqlite3
DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
print("=== agent_tasks.status 分布 ===")
cur.execute("SELECT status, COUNT(*) c FROM agent_tasks GROUP BY status ORDER BY c DESC")
for s, c in cur.fetchall():
    print(f"  {s!r:20} x{c}")
conn.close()
