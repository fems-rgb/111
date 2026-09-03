import re
p = "backend/app/services/project_service.py"
src = open(p, encoding="utf-8").read()

old = '''        sv = st.value if hasattr(st, "value") else st
        if sv == "completed":
            s[1] += 1'''
new = '''        sv = st.value if hasattr(st, "value") else st
        sv = str(sv).strip().lower() if sv is not None else ""
        if sv in ("completed", "complete", "done", "success", "succeeded"):
            s[1] += 1'''

if old in src:
    src = src.replace(old, new)
    open(p, "w", encoding="utf-8").write(src)
    print("[OK] 进度统计已修复（大小写不敏感）")
    print("  旧: sv == \"completed\"  -> 匹配不到 COMPLETED")
    print("  新: str(sv).lower() in (...)  -> 匹配 COMPLETED/Completed/completed")
else:
    print("[WARN] 未匹配到原文，打印当前统计代码:")
    m = re.search(r"async def get_user_projects_with_progress.*?(?=\nasync def |\Z)", src, re.S)
    if m:
        for i, l in enumerate(m.group(0).split("\n"), 1):
            if "sv" in l or "s[1]" in l or "s[0]" in l:
                print("   " + l.rstrip())

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[语法校验] OK")
except py_compile.PyCompileError as e:
    print("[语法错误]", e)
