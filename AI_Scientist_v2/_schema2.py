import sqlite3
DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
print("表列表:")
for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print("  -", r["name"])
print("\nprojects 实际列:")
for r in c.execute("PRAGMA table_info(projects)"):
    print("  ", r["name"], r["type"])

# 找含 methods/rationale/paper_title/hypotheses 的表
print("\n含领域字段的表:")
for t in [r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
    cols = [r["name"] for r in c.execute(f"PRAGMA table_info({t})")]
    hit = [col for col in cols if col in ("methods","rationale","paper_title","paper_abstract","experiments","results","hypotheses","research_question")]
    if hit:
        print(f"  {t}: {hit}")
        # 抽样一行
        try:
            row = c.execute(f"SELECT * FROM {t} ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                print("    样例:", dict(row))
        except Exception as e:
            print("    读取失败:", e)
c.close()
