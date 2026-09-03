lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("修复后 L39")
print("="*64)
print("  L39|", lines[38].rstrip()[:170])

print()
print("="*64)
print("resume_mode 全部出现位置")
print("="*64)
for i, l in enumerate(lines):
    if "resume_mode" in l:
        print("%4d| %s" % (i+1, l.rstrip()[:140]))
