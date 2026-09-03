import sqlite3

c = sqlite3.connect("backend/zhixing.db")
print("有 title 的行:", c.execute(
    "SELECT COUNT(*) FROM science_questions WHERE title IS NOT NULL AND title != ''"
).fetchone()[0])
print("title 为空的行:", c.execute(
    "SELECT COUNT(*) FROM science_questions WHERE title IS NULL OR title = ''"
).fetchone()[0])
print()
print("前3条完整数据:")
for r in c.execute("SELECT * FROM science_questions ORDER BY id LIMIT 3"):
    print(" ", r)