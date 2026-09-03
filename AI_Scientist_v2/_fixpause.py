p = "backend/app/api/v1/projects.py"
src = open(p, encoding="utf-8").read()

print("="*64)
print("修复前 pause 接口")
print("="*64)
for i in range(158, 168):
    print("  L%d| %s" % (i+1, src.split(chr(10))[i].rstrip()[:110]))

# 修复：给两处异步调用加 await
old = """    await _get_project(db, project_id, user.id)
    orchestrator.pause_project(project_id)
    return {"message": "项目已暂停"}"""

new = """    await _get_project(db, project_id, user.id)
    await orchestrator.pause_project(project_id)
    return {"message": "项目已暂停"}"""

if old in src:
    src = src.replace(old, new, 1)
    print("\n[OK] 已加 await：orchestrator.pause_project")
else:
    print("\n[WARN] 精确锚点未匹配，尝试逐行：")
    lines = src.split("\n")
    for i, l in enumerate(lines):
        if "orchestrator.pause_project" in l and "await" not in l:
            lines[i] = l.replace("    orchestrator.pause_project", "    await orchestrator.pause_project")
            print("  L%d 已加 await" % (i+1))
    src = "\n".join(lines)

# 同样检查 restart 里的 start_project（L187）是否也没 await
if "run_result = await orchestrator.start_project" not in src and "run_result = orchestrator.start_project" in src:
    src = src.replace(
        "run_result = orchestrator.start_project",
        "run_result = await orchestrator.start_project"
    )
    print("[OK] 顺便修复 restart: start_project 加 await")

open(p, "w", encoding="utf-8").write(src)

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("\n[syntax] OK")
except py_compile.PyCompileError as e:
    print("\n[syntax] L%d: %s" % (e.lineno, e.msg))

print("\n" + "="*64)
print("修复后 pause 接口")
print("="*64)
lines = open(p, encoding="utf-8").read().split("\n")
for i in range(158, 168):
    print("  L%d| %s" % (i+1, lines[i].rstrip()[:110]))
