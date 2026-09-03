import sqlite3
db = "D:/AI_Scientist/AI_Scientist/backend/zhixing.db"
c = sqlite3.connect(db)
cur = c.cursor()

print("修复前:")
for r in cur.execute("SELECT id, status FROM projects ORDER BY id"):
    print("  project=%-4s %s" % (r[0], r[1]))
for r in cur.execute("SELECT project_id, status, COUNT(*) FROM agent_tasks WHERE status IN (\"RUNNING\",\"PENDING\") GROUP BY project_id, status"):
    print("  tasks project=%-4s %-8s n=%s" % (r[0], r[1], r[2]))

# 只解锁卡住的：PENDING/RUNNING -> FAILED（不碰已完成的，不删任何数据）
cur.execute("UPDATE agent_tasks SET status=\"FAILED\" WHERE status IN (\"RUNNING\",\"PENDING\")")
n1 = cur.rowcount
cur.execute("UPDATE projects SET status=\"FAILED\" WHERE status=\"RUNNING\"")
n2 = cur.rowcount
c.commit()

print()
print("修复后 (tasks=%d, projects=%d):" % (n1, n2))
for r in cur.execute("SELECT id, status FROM projects ORDER BY id"):
    print("  project=%-4s %s" % (r[0], r[1]))
c.close()
