lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("当前 L39-40 (签名)")
print("="*64)
for i in range(38, 42):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:130]))

print()
print("="*64)
print("resume_mode 出现情况")
print("="*64)
for i, l in enumerate(lines):
    if "resume_mode" in l:
        print("%4d| %s" % (i+1, l.rstrip()[:130]))
