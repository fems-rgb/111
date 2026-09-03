import os, re, sqlite3

DB = "D:/AI_Scientist/AI_Scientist/backend/zhixing.db"

print("="*64)
print("[A] 数据库当前状态")
print("="*64)
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
print("  projects:")
for r in c.execute("SELECT id,title,status FROM projects ORDER BY id"):
    print("    id=%-4s %-10s %s" % (r["id"], r["status"], str(r["title"])[:42]))
print()
n = c.execute("SELECT COUNT(*) FROM question_tasks").fetchone()[0]
print("  question_tasks 剩余: %s" % n)
for r in c.execute("SELECT id,question_id,status FROM question_tasks"):
    print("    task id=%-4s qid=%-4s %s" % (r["id"], r["question_id"], r["status"]))
print()
print("  agent_tasks:")
for r in c.execute("SELECT project_id,status,COUNT(*) n FROM agent_tasks GROUP BY project_id,status"):
    print("    project=%-4s %-10s n=%s" % (r["project_id"], r["status"], r["n"]))
c.close()

print()
print("="*64)
print("[B] projects.py 删除接口完整代码")
print("="*64)
src = open("backend/app/api/v1/projects.py", encoding="utf-8").read()
i = src.find("@router.delete")
if i >= 0:
    j = src.find("\n@router.", i + 10)
    if j < 0:
        j = len(src)
    for n, l in enumerate(src[i:j].split("\n"), 1):
        print("%3d| %s" % (n, l.rstrip()[:110]))
else:
    print("  未找到 delete 路由")

print()
print("="*64)
print("[C] 后端 progress 赋值（找硬编码 30/50 之类）")
print("="*64)
for root, dirs, files in os.walk("backend/app"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fn in files:
        if not fn.endswith(".py"):
            continue
        fp = os.path.join(root, fn)
        try:
            for n, l in enumerate(open(fp, encoding="utf-8", errors="ignore"), 1):
                if "progress" in l and re.search(r"progress\s*=\s*\d+", l):
                    print("  %s L%d| %s" % (fp.replace("\\","/"), n, l.strip()[:100]))
        except Exception:
            pass

print()
print("="*64)
print("[D] 前端 store 是否透传 progress/total_steps")
print("="*64)
for root, dirs, files in os.walk("frontend/src/stores"):
    for fn in files:
        if not fn.endswith((".ts", ".js")):
            continue
        fp = os.path.join(root, fn)
        try:
            for n, l in enumerate(open(fp, encoding="utf-8", errors="ignore"), 1):
                if "progress" in l.lower() or "fetchProjects" in l:
                    print("  %s L%d| %s" % (fn, n, l.strip()[:100]))
        except Exception:
            pass

print()
print("="*64)
print("[E] 进度聚合修复后的真实值（模拟后端计算）")
print("="*64)
c = sqlite3.connect(DB)
for pid in [1, 2, 3]:
    rows = c.execute("SELECT status, COUNT(*) FROM agent_tasks WHERE project_id=? GROUP BY status", (pid,)).fetchall()
    if not rows:
        continue
    total = sum(x[1] for x in rows)
    done = sum(x[1] for x in rows if str(x[0]).strip().lower() == "completed")
    pct = round(done / total * 100) if total else 0
    print("  project %-4s total=%-3s completed=%-3s -> progress=%s%%" % (pid, total, done, pct))
c.close()
