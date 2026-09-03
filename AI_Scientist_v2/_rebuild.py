lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("L86-112 完整（找重建循环的结束点）")
print("="*64)
for i in range(85, 115):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:140]))
