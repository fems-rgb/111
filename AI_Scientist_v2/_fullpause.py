lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
start = None
for i, l in enumerate(lines):
    if "def pause_project" in l.strip():
        start = i
        break
# 打印整个函数
if start:
    for i in range(start, min(start + 60, len(lines))):
        print("%4d| %s" % (i+1, lines[i].rstrip()[:110]))
        if i > start and lines[i].strip().startswith("def "):
            break
