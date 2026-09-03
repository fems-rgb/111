print("="*64)
print("[1] 按钮区 L32-37")
print("="*64)
lines = open("frontend/src/views/workspace/ProjectDetail.vue", encoding="utf-8").read().split("\n")
for i in range(31, 37):
    print("  L%d| %s" % (i+1, lines[i].rstrip()[:140]))

print()
print("="*64)
print("[2] handleResume 定义")
print("="*64)
found = False
for i, l in enumerate(lines):
    if "async function handleResume" in l:
        found = True
        for j in range(i, min(i+12, len(lines))):
            print("  L%d| %s" % (j+1, lines[j].rstrip()[:150]))
if not found:
    print("  ❌ 未找到！需要添加")

print()
print("="*64)
print("[3] projectApi.resume")
print("="*64)
ts = open("frontend/src/api/modules/project.ts", encoding="utf-8").read()
print("  resume: defined =", "resume:" in ts)
if "resume:" in ts:
    for l in ts.split("\n"):
        if "resume:" in l:
            print("    " + l.strip()[:120])
