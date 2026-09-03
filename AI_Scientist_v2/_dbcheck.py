import os, re, glob, sqlite3

print("="*60)
print("[1] 所有数据库文件")
print("="*60)
for f in glob.glob("**/*.db", recursive=True) + glob.glob("**/*.sqlite*", recursive=True):
    if "node_modules" in f: continue
    try:
        c = sqlite3.connect(f)
        n = c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        print("  %-52s projects=%s" % (f, n))
        c.close()
    except Exception as e:
        print("  %-52s ERR %s" % (f, str(e)[:40]))

print()
print("="*60)
print("[2] 后端配置的数据库路径")
print("="*60)
for p in ["backend/app/database/session.py", "backend/app/core/config.py", "backend/.env", ".env"]:
    if os.path.exists(p):
        for i, l in enumerate(open(p, encoding="utf-8", errors="ignore"), 1):
            if any(k in l.lower() for k in ("database_url", "sqlite", "zhixing", "db_url")):
                print("  %s L%d| %s" % (p, i, l.strip()[:100]))
