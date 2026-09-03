import os
p = "frontend/src/stores/project.ts"
if os.path.exists(p):
    print("="*60)
    print("project.ts (L20-75)")
    print("="*60)
    lines = open(p, encoding="utf-8").read().split("\n")
    for i in range(19, min(75, len(lines))):
        print("%4d| %s" % (i+1, lines[i].rstrip()[:110]))
else:
    print("未找到 project.ts")
