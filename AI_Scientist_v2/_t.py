import sqlite3
c = sqlite3.connect("backend/zhixing.db")
print("total:", c.execute("SELECT COUNT(*) FROM science_questions").fetchone()[0])
print("has_title:", c.execute("SELECT COUNT(*) FROM science_questions WHERE title IS NOT NULL AND length(title)>0").fetchone()[0])
