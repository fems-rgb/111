# ── 1) 后端 projects.py 全部路由清单 ──
lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
print("="*64)
print("projects.py 路由 + 函数")
print("="*64)
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith("@router.") or (s.startswith(("async def ", "def ")) and not s.startswith("def _")):
        print("%4d| %s" % (i+1, s[:110]))
