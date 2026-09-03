lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("pause_project 完整实现（L613 起，到下一个 def）")
print("="*64)
start = None
for i, l in enumerate(lines):
    if l.strip().startswith("def pause_project") or l.strip().startswith("async def pause_project"):
        start = i
        break
if start is None:
    print("未找到 pause_project 定义！")
else:
    for i in range(start, min(start + 45, len(lines))):
        s = lines[i].rstrip()
        print("%4d| %s" % (i+1, s[:110]))
        if i > start and (s.strip().startswith("def ") or s.strip().startswith("async def ")):
            break
