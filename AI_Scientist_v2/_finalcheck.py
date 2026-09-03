print("="*64)
print("[前端] 三处检查")
print("="*64)
vue = open("frontend/src/views/workspace/ProjectDetail.vue", encoding="utf-8").read()
ts = open("frontend/src/api/modules/project.ts", encoding="utf-8").read()

print("  1) 按钮调 handleResume:", '@click="handleResume"' in vue)
print("  2) handleResume 定义:", "async function handleResume" in vue)
print("  3) projectApi.resume:", "resume:" in ts)

print()
print("="*64)
print("[后端] 两处检查")
print("="*64)
orch = open("backend/app/agents/orchestrator.py", encoding="utf-8").read()
proj = open("backend/app/api/v1/projects.py", encoding="utf-8").read()
print("  1) resume_mode 参数 (L39):", "resume_mode: bool = False" in orch)
print("  2) resume 分支 (L76):", "if resume_mode:" in orch)
print("  3) 跳过重建 (L88):", "if resume_mode:" in orch)
print("  4) resume 路由:", "@router.post(\"/{project_id}/resume\")" in proj)
print("  5) resume_mode=True 调用:", "resume_mode=True" in proj)

print()
print("="*64)
print("[语法校验]")
print("="*64)
import py_compile
try:
    py_compile.compile("backend/app/agents/orchestrator.py", doraise=True)
    print("  orchestrator.py OK")
except py_compile.PyCompileError as e:
    print("  orchestrator.py L%d: %s" % (e.lineno, e.msg))
try:
    py_compile.compile("backend/app/api/v1/projects.py", doraise=True)
    print("  projects.py OK")
except py_compile.PyCompileError as e:
    print("  projects.py L%d: %s" % (e.lineno, e.msg))
