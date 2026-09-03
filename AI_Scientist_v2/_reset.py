import sqlite3

DB = "D:/AI_Scientist/AI_Scientist/backend/zhixing.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("重置前: project 1 status =", c.execute("SELECT status FROM projects WHERE id=1").fetchone()["status"])

# 模拟：跑到第 6 步暂停（前 6 完成，第 7 是 RUNNING，8-9 未开始）
# 先全部重置
c.execute("UPDATE agent_tasks SET status='PENDING', output_data=NULL WHERE project_id=1")
rows = c.execute("SELECT id, step_order, agent_name FROM agent_tasks WHERE project_id=1 ORDER BY step_order").fetchall()
for t in rows:
    if t["step_order"] <= 6:
        c.execute("UPDATE agent_tasks SET status='COMPLETED', output_data='模拟已完成数据' WHERE id=?", (t["id"],))
    elif t["step_order"] == 7:
        c.execute("UPDATE agent_tasks SET status='RUNNING' WHERE id=?", (t["id"],))  # 暂停时正在执行
# project 设为 PAUSED
c.execute("UPDATE projects SET status='PAUSED' WHERE id=1")
c.commit()

print("\n重置后状态:")
print("  project.status =", c.execute("SELECT status FROM projects WHERE id=1").fetchone()["status"])
print("  tasks:")
for t in c.execute("SELECT step_order, agent_name, status FROM agent_tasks WHERE project_id=1 ORDER BY step_order"):
    print("    step %s %-25s %s" % (t["step_order"], t["agent_name"], t["status"]))
c.close()
print("\n✅ 现在可以测试 resume：应该从 step 7 (RUNNING→PENDING) 继续")
