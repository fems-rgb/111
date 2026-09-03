import os, re, sqlite3

DB = "backend/zhixing.db"
print("="*60)
print("[A] 删除诊断：项目与任务状态")
print("="*60)
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
try:
    rows = c.execute("SELECT id, title, status FROM projects ORDER BY id").fetchall()
    print("projects (%d):" % len(rows))
    for r in rows:
        print("  id=%-4s status=%-12s %s" % (r["id"], r["status"], str(r["title"])[:44]))
except Exception as e:
    print("  ERR", e)
print()
try:
    for r in c.execute("SELECT project_id, status, COUNT(*) n FROM agent_tasks GROUP BY project_id, status"):
        print("  agent_tasks project=%-4s status=%-12s n=%s" % (r["project_id"], r["status"], r["n"]))
except Exception as e:
    print("  ERR", e)
print()
try:
    for r in c.execute("SELECT id, question_id, status FROM question_tasks"):
        print("  question_tasks:", dict(r))
except Exception as e:
    print("  ERR", e)
print()
for t in ("experiment_runs", "hypotheses", "agent_tasks", "documents", "projects"):
    try:
        n = c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("  表 %-18s 行数=%s" % (t, n))
    except Exception:
        pass
c.close()

print()
print("="*60)
print("[B] 后端：项目列表接口")
print("="*60)
p = "backend/app/api/v1/projects.py"
if os.path.exists(p):
    src = open(p, encoding="utf-8").read()
    m = re.search(r"@router\.get.*?\nasync def list_projects.*?(?=\n@router|\Z)", src, re.S)
    if m:
        for l in m.group(0).split("\n")[:55]:
            print("  " + l.rstrip()[:110])
    else:
        for i, l in enumerate(src.split("\n"), 1):
            if "@router.get" in l or "async def list" in l or "async def delete" in l:
                print("  L%-4d %s" % (i, l.strip()[:100]))

print()
print("="*60)
print("[C] SSE 事件定义")
print("="*60)
for root, dirs, files in os.walk("backend/app"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fn in files:
        if not fn.endswith(".py"): continue
        fp = os.path.join(root, fn)
        try:
            for i, l in enumerate(open(fp, encoding="utf-8", errors="ignore"), 1):
                s = l.strip()
                if "class Events" in s or re.match(r"^(AGENT_STEP_UPDATE|AGENT_COMPLETED|PROJECT_|PROGRESS)\s*=", s):
                    print("  %s L%d| %s" % (fp.replace("\\","/"), i, s[:95]))
        except Exception:
            pass

print()
print("="*60)
print("[D] 前端：题库进度来源")
print("="*60)
fv = "frontend/src/views/workspace/QuestionsView.vue"
if os.path.exists(fv):
    for i, l in enumerate(open(fv, encoding="utf-8"), 1):
        if any(k in l for k in ("progress", "POLL_INTERVAL", "percent", "EventSource", "eventSource", "onmessage")):
            print("  L%-5d %s" % (i, l.strip()[:110]))

print()
print("="*60)
print("[E] 前端：工作台项目列表文件")
print("="*60)
for root, dirs, files in os.walk("frontend/src"):
    for fn in files:
        if fn.endswith(".vue") and any(k in fn.lower() for k in ("workspace", "project", "home")):
            print("  " + os.path.join(root, fn).replace("\\","/"))
