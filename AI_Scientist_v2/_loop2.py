lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("_execute_pipeline: task 遍历逻辑 (L110-170)")
print("="*64)
for i in range(109, 175):
    s = lines[i].rstrip()
    print("%4d| %s" % (i+1, s[:120]))
