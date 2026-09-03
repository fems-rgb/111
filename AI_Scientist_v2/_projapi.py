# 前端 project.ts 的完整 API 定义
lines = open("frontend/src/api/modules/project.ts", encoding="utf-8").read().split("\n")
print("="*64)
print("project.ts API")
print("="*64)
for i, l in enumerate(lines):
    print("%4d| %s" % (i+1, l.rstrip()[:110]))
