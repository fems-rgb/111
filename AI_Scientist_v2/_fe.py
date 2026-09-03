import os
print("="*60)
print("Workspace 相关 vue 文件")
print("="*60)
for root, dirs, files in os.walk("frontend/src/views"):
    for fn in files:
        if fn.endswith(".vue"):
            fp = os.path.join(root, fn)
            try:
                t = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if any(k in t for k in ("projectApi", "listProjects", "projects.value", "研究项目")):
                print("  " + fp.replace("\\","/"))
                for i, l in enumerate(t.split("\n"), 1):
                    if any(k in l for k in ("projectApi", "listProjects", "p.progress", "progress", "<n-progress", "a-progress")):
                        print("      L%-4d %s" % (i, l.strip()[:100]))
print()
print("="*60)
print("ProjectListItem 模型定义")
print("="*60)
p = "backend/app/schemas/project.py"
for pp in ("backend/app/schemas/project.py", "backend/app/api/v1/projects.py"):
    if os.path.exists(pp):
        src = open(pp, encoding="utf-8").read()
        m = re.search(r"class ProjectListItem.*?(?=\nclass |\Z)", src, re.S) if "class ProjectListItem" in src else None
        if m:
            print("  [%s]" % pp)
            for l in m.group(0).split("\n")[:30]:
                print("    " + l.rstrip()[:100])
