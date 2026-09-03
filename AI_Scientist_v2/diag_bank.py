import os, sys, sqlite3

out = []
def add(s=""): out.append(s)
BACKEND = os.path.abspath("backend")
DB = os.path.join(BACKEND, "zhixing.db")

add("="*64); add("诊断：导入125题后刷新为空"); add("="*64)

# ---------- [1] 数据库连接与全部表 ----------
add(""); add("[1] 数据库基本信息")
conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
add("  文件: %s" % DB)
add("  大小: %.0f KB" % (os.path.getsize(DB) / 1024))
add("  存在: %s" % os.path.exists(DB))

c = conn.cursor()
tables = [r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
add(""); add("[2] 所有表 (%d 个):" % len(tables))
for t in tables:
    add("    - %s" % t)

# ---------- [3] 找题库相关表 ----------
add(""); add("[3] 候选题库表（question* / science* / bank*）")
cand = [t for t in tables if any(k in t.lower() for k in ("question", "science", "bank", "task", "topic"))]
if not cand:
    cand = tables
for t in cand:
    try:
        n = c.execute("SELECT COUNT(*) n FROM %s" % t).fetchone()["n"]
        cols = [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]
        add("    %-20s 行数=%-6s 列=%s" % (t, n, cols[:8]))
    except Exception as e:
        add("    %-20s ERR %s" % (t, e))

# ---------- [4] 逐表查 Science 125 内容 ----------
add(""); add("[4] 逐表搜索含 '宇宙'/'意识'/'物理定律' 的记录（确认到底存没存进去）")
kw = ["宇宙", "意识", "物理定律", "人类寿命", "器官再生"]
for t in tables:
    cols = [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]
    text_cols = [col for col in cols if col.lower() in ("question", "title", "content", "text", "name", "topic")]
    if not text_cols:
        continue
    for col in text_cols[:2]:
        for w in kw:
            try:
                r = c.execute("SELECT COUNT(*) n FROM %s WHERE %s LIKE ?" % (t, col), ("%%%s%%" % w,)).fetchone()
                if r["n"] > 0:
                    add("    %-18s %-10s 含 '%s' = %d 行" % (t, col, w, r["n"]))
                    break
            except Exception:
                break
        else:
            continue
        break

# ---------- [5] 前端列表 API 对应的表 ----------
add(""); add("[5] 前端题库页面调用的 API（grep 线索）")
fp = os.path.join(BACKEND, "app", "api", "v1")
if os.path.isdir(fp):
    for root, _, files in os.walk(fp):
        for f in files:
            if not f.endswith(".py"): continue
            p = os.path.join(root, f)
            for i, line in enumerate(open(p, encoding="utf-8"), 1):
                if any(k in line for k in ("question", "science125", "SCIENCE_125", "/questions", "question_tasks")):
                    add("    %s:%d  %s" % (os.path.relpath(p, BACKEND), i, line.strip()[:110]))

# ---------- [6] 最新插入的 5 条记录（哪个表在涨）----------
add(""); add("[6] 每张表最新 1 条记录的 id 与时间字段（看导入落在哪张表）")
for t in tables:
    cols = [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]
    id_col = next((x for x in ("id", "question_id", "task_id") if x in cols), None)
    time_col = next((x for x in ("created_at", "create_time", "updated_at", "time") if x in cols), None)
    if not id_col: continue
    try:
        row = c.execute("SELECT * FROM %s ORDER BY %s DESC LIMIT 1" % (t, id_col)).fetchone()
        if row:
            d = dict(row)
            ts = d.get(time_col, "") if time_col else ""
            add("    %-18s 最新 id=%-6s %s" % (t, d.get(id_col), ts))
    except Exception:
        pass

conn.close()
add(""); add("="*64)
open("diag_bank_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))