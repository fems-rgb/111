print("="*64)
print("[1] 前端按钮区（应有 启动/暂停/继续/重启 四个）")
print("="*64)
lines = open("frontend/src/views/workspace/ProjectDetail.vue", encoding="utf-8").read().split("\n")
for i in range(31, 37):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:120]))

print()
print("="*64)
print("[2] 后端 pause 接口（应：立即改 DB + 内存标志）")
print("="*64)
lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
for i in range(158, 170):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:120]))

print()
print("="*64)
print("[3] progress_sync 是否已注册到 lifespan")
print("="*64)
lines = open("backend/app/main.py", encoding="utf-8").read().split("\n")
for i in range(27, 33):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:120]))
