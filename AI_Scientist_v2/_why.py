import os, re, sqlite3, glob

DB = "D:/AI_Scientist/AI_Scientist/backend/zhixing.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row

print("="*64)
print("[A] project 1/2 的关联数据")
print("="*64)
c2 = c.cursor()
for t, col in [("agent_tasks","project_id"), ("experiment_runs","project_id"),
               ("hypotheses","project_id"), ("documents","project_id"),
               ("pipeline_runs","project_id"), ("iteration_records","project_id"),
               ("trace_records","project_id")]:
    try:
        n = c2.execute("SELECT COUNT(*) FROM %s WHERE %s IN (1,2)" % (t, col)).fetchone()[0]
        print("  %-20s 关联 %s 条" % (t, n))
    except Exception as e:
        print("  %-20s ERR %s" % (t, str(e)[:50]))

print()
print("="*64)
print("[B] document_path 指向的文件是否存在（老项目常见坑）")
print("="*64)
try:
    for r in c2.execute("SELECT id, project_id, document_path FROM agent_tasks WHERE project_id IN (1,2) AND document_path IS NOT NULL AND document_path != ''"):
        p = r["document_path"]
        ex = os.path.exists(p)
        print("  task=%-4s project=%-3s [%s] %s" % (r["id"], r["project_id"], "OK " if ex else "MISS", str(p)[:60]))
except Exception as e:
    print("  ERR", e)

print()
print("="*64)
print("[C] cleanup.py 清理函数是否有容错")
print("="*64)
p = "backend/app/utils/cleanup.py"
if os.path.exists(p):
    for i, l in enumerate(open(p, encoding="utf-8"), 1):
        print("%4d| %s" % (i, l.rstrip()[:105]))
else:
    print("  未找到 cleanup.py")

print()
print("="*64)
print("[D] 删除接口全文 (projects.py 204-262)")
print("="*64)
lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
for i in range(203, min(262, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:108]))
c.close()
