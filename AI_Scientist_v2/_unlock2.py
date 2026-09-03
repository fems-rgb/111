import sqlite3
db = "D:/AI_Scientist/AI_Scientist/backend/zhixing.db"
c = sqlite3.connect(db)
cur = c.cursor()

print("修复前:")
for r in cur.execute('SELECT id,status FROM projects ORDER BY id'):
    print("  project=%-4s %s" % (r[0], r[1]))
for r in cur.execute("SELECT id,status FROM question_tasks"):
    print("  qt id=%-4s %s" % (r[0], r[1]))

cur.execute("UPDATE agent_tasks SET status='FAILED' WHERE status IN ('RUNNING','PENDING','running','pending')")
n1 = cur.rowcount
cur.execute("UPDATE projects SET status='FAILED' WHERE status IN ('RUNNING','running')")
n2 = cur.rowcount
cur.execute("UPDATE question_tasks SET status='failed' WHERE status IN ('running','pending','RUNNING','PENDING')")
n3 = cur.rowcount
c.commit()

print()
print("已解锁: agent_tasks=%d, projects=%d, question_tasks=%d" % (n1, n2, n3))
print()
print("修复后:")
for r in cur.execute("SELECT id,status FROM projects ORDER BY id"):
    print("  project=%-4s %s" % (r[0], r[1]))
c.close()
