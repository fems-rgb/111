lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("完整签名 (L39-40)")
print("="*64)
print("  L39|", lines[38].rstrip()[:150])
print("  L40|", lines[39].rstrip()[:150])

print()
print("="*64)
print("L70-100 完整（含 resume_mode 分支）")
print("="*64)
for i in range(69, 102):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:135]))
