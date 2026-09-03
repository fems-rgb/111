p = "backend/app/api/v1/projects.py"
src = open(p, encoding="utf-8").read()

old = """@router.post("/{project_id}/pause")
async def pause(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, project_id, user.id)
    await orchestrator.pause_project(project_id)
    return {"message": "项目已暂停"}"""

new = """@router.post("/{project_id}/pause")
async def pause(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project(db, project_id, user.id)
    # 1) 置内存标志 -> 循环下一轮检测到会自动 PAUSED（兜底）
    orchestrator.pause_project(project_id)
    # 2) 立即持久化状态，让前端 fetchProject 秒级感知（即时反馈）
    if project.status == ProjectStatus.RUNNING:
        project.status = ProjectStatus.PAUSED
        await db.commit()
    return {"message": "项目已暂停"}"""

if old in src:
    src = src.replace(old, new, 1)
    print("[OK] pause 接口已改为：立即改 DB + 内存标志")
else:
    print("[WARN] 锚点未匹配，当前 L159-167:")
    lines = src.split("\n")
    for i in range(158, 168):
        print("  L%d| %s" % (i+1, lines[i].rstrip()[:110]))

open(p, "w", encoding="utf-8").write(src)

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] OK")
except py_compile.PyCompileError as e:
    print("[syntax] L%d: %s" % (e.lineno, e.msg))
