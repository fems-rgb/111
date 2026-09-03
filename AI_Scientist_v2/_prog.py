import re
p = "backend/app/services/project_service.py"
src = open(p, encoding="utf-8").read()
m = re.search(r"async def get_user_projects_with_progress.*?(?=\nasync def |\Z)", src, re.S)
if m:
    print("="*60)
    print("get_user_projects_with_progress")
    print("="*60)
    for i, l in enumerate(m.group(0).split("\n"), 1):
        print("%3d| %s" % (i, l.rstrip()[:115]))
else:
    print("未找到该函数，搜索 progress 相关:")
    for i, l in enumerate(src.split("\n"), 1):
        if "progress" in l.lower():
            print("  L%-4d %s" % (i, l.strip()[:100]))
