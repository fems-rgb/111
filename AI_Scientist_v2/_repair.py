import re, sqlite3

ts = open("frontend/src/data/science125.ts", encoding="utf-8").read()
d = {}
for m in re.finditer(r'{\s*id:\s*(\d+),\s*question:\s*"([^"]*)"', ts):
    d[int(m.group(1))] = m.group(2)

print("parsed:", len(d))
if not d:
    raise SystemExit("解析失败")

c = sqlite3.connect("backend/zhixing.db")
cur = c.cursor()

cur.execute("DELETE FROM science_questions WHERE title IS NULL OR length(title)=0")
cleared = cur.rowcount
print("cleared:", cleared)

for i, title in d.items():
    cur.execute(
        "INSERT INTO science_questions"
        "(question_id,title,category,difficulty,source,is_active,sort_order)"
        "VALUES(?,?,?,?,?,?,?)",
        (i, title, "science125", "medium", "batch_import", 1, i)
    )
c.commit()

print("inserted:", len(d))
print("total:", cur.execute("SELECT COUNT(*) FROM science_questions").fetchone()[0])
print("has_title:", cur.execute("SELECT COUNT(*) FROM science_questions WHERE length(title)>0").fetchone()[0])
for i in range(1, 4):
    print(" ", i, d.get(i))
