lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
print("="*64)
print("[A] resume 接口完整内容")
print("="*64)
start = None
for i, l in enumerate(lines):
    if "@router.post(\"/{project_id}/resume\")" in l:
        start = i
        break
if start is None:
    print("❌ 未找到 resume 接口！需要添加")
else:
    for i in range(start, min(start + 30, len(lines))):
        s = lines[i].rstrip()
        print("%4d| %s" % (i+1, s[:150]))
        if i > start and (s.strip().startswith("def ") or s.strip().startswith("async def ")) and i != start:
            break

print()
print("="*64)
print("[B] resume 接口数量检查")
print("="*64)
print("  resume 路由出现次数:", sum(1 for l in lines if "@router.post(\"/{project_id}/resume\")" in l))
