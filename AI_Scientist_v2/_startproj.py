lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("start_project 完整实现 (L39 起)")
print("="*64)
for i in range(38, 115):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:120]))
