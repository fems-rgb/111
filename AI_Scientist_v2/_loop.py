lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")

print("="*64)
print("[A] _execute_pipeline 循环结构（找 is_running / _running_projects 检查点）")
print("="*64)
# 找 _execute_pipeline 定义
start = None
for i, l in enumerate(lines):
    if "_execute_pipeline" in l and ("def " in l or "async def " in l):
        start = i
        break
if start is None:
    print("未找到 _execute_pipeline")
else:
    end = min(start + 200, len(lines))
    for i in range(start, end):
        s = lines[i].rstrip()
        if i > start and s.strip().startswith("def ") and i != start:
            break
        # 只打印关键行：循环、is_running、step、sleep、checkpoint
        if any(k in s for k in ["is_running", "_running_projects", "while ", "for ", "step", "await ", "checkpoint", "status", "PAUSED", "cancel"]):
            print("%4d| %s" % (i+1, s[:115]))

print()
print("="*64)
print("[B] _running_projects 定义 + 类初始化")
print("="*64)
for i, l in enumerate(lines):
    if "_running_projects" in l or "__init__" in l:
        print("%4d| %s" % (i+1, l.rstrip()[:110]))
