lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
print("="*64)
print("pause 接口 (L159 起)")
print("="*64)
for i in range(157, min(200, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:110]))
