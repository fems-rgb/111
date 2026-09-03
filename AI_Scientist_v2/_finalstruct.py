lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("修改后 L74-115 完整结构")
print("="*64)
for i in range(73, 120):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:145]))
