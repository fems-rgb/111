lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
print("="*64)
print("start 接口完整实现 (L123-158)")
print("="*64)
for i in range(122, 160):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:115]))
