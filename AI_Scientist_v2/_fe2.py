import os, re

print("="*60)
print("[1] ProjectListItem 是否含 progress 字段")
print("="*60)
for pp in ("backend/app/schemas/project.py", "backend/app/api/v1/projects.py"):
    if os.path.exists(pp):
        src = open(pp, encoding="utf-8").read()
        if "class ProjectListItem" in src:
            m = re.search(r"class ProjectListItem.*?(?=\nclass |\Z)", src, re.S)
            print("  [%s]" % pp)
            for l in m.group(0).split("\n")[:30]:
                print("    " + l.rstrip()[:100])
        else:
            print("  [%s] 无 ProjectListItem" % pp)

print()
print("="*60)
print("[2] DashboardView.vue 进度条上下文 (L160-185)")
print("="*60)
p = "frontend/src/views/workspace/DashboardView.vue"
lines = open(p, encoding="utf-8").read().split("\n")
for i in range(158, min(186, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:115]))

print()
print("="*60)
print("[3] DashboardView 项目列表数据来源")
print("="*60)
for i, l in enumerate(lines, 1):
    s = l.strip()
    if any(k in s for k in ("projectApi", "listProjects", "projects.value", "loadProjects", "fetchProjects", "v-for")):
        print("  L%-4d %s" % (i, s[:110]))

print()
print("="*60)
print("[4] 删除接口（找为什么删不掉）")
print("="*60)
p2 = "backend/app/api/v1/projects.py"
src2 = open(p2, encoding="utf-8").read()
m = re.search(r"@router\.delete.*?(?=\n@router|\Z)", src2, re.S)
if m:
    for i, l in enumerate(m.group(0).split("\n"), 1):
        print("%3d| %s" % (i, l.rstrip()[:110]))
else:
    for i, l in enumerate(src2.split("\n"), 1):
        if "delete" in l.lower():
            print("  L%-4d %s" % (i, l.strip()[:100]))
