import sqlite3
print("="*60)
print("原工作区数据库（第二版实际连接的）")
print("="*60)
try:
    c = sqlite3.connect("D:/AI_Scientist/AI_Scientist/backend/zhixing.db")
    c.row_factory = sqlite3.Row
    print("  projects:", c.execute("SELECT COUNT(*) FROM projects").fetchone()[0])
    for r in c.execute("SELECT id, title, status FROM projects ORDER BY id"):
        print("    id=%-4s %-12s %s" % (r["id"], r["status"], str(r["title"])[:45]))
    print()
    print("  agent_tasks:")
    for r in c.execute("SELECT project_id, status, COUNT(*) n FROM agent_tasks GROUP BY project_id, status"):
        print("    project=%-4s status=%-12s n=%s" % (r["project_id"], r["status"], r["n"]))
    c.close()
except Exception as e:
    print("  ERR", e)
