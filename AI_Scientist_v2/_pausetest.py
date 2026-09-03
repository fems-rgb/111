import sqlite3
DB = "D:/AI_Scientist/AI_Scientist/backend/zhixing.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row

print("当前 project 状态:")
for p in c.execute("SELECT id, title, status FROM projects ORDER BY id DESC LIMIT 5"):
    print("  project=%-3s %-12s %s" % (p["id"], p["status"], str(p["title"])[:50]))

print()
print("要暂停题库任务对应的 project=1，直接测接口逻辑:")
p = c.execute("SELECT * FROM projects WHERE id=1").fetchone()
print("  project 1 当前 status =", p["status"])
print()
print("pause 接口应该: project.status = PAUSED, 并返回 200")
print("如果前端调的是 POST /projects/1/pause -> 检查后端日志")
c.close()
