p = "backend/app/api/v1/projects.py"
src = open(p, encoding="utf-8").read()

# 在 pause 接口之后插入 resume 接口
anchor = """    if project.status == ProjectStatus.RUNNING:
        project.status = ProjectStatus.PAUSED
        await db.commit()
    return {"message": "项目已暂停"}"""

resume = """    if project.status == ProjectStatus.RUNNING:
        project.status = ProjectStatus.PAUSED
        await db.commit()
    return {"message": "项目已暂停"}


@router.post("/{project_id}/resume")
async def resume(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    \"\"\"从暂停处继续：保留已完成的步骤，从下一个 pending 步骤接着跑\"\"\"
    from app.core.exceptions import ProjectNotReadyError, AgentException
    project = await _get_project(db, project_id, user.id)
    if project.status == ProjectStatus.RUNNING:
        return {"message": "项目已在运行中"}
    if project.status != ProjectStatus.PAUSED:
        raise ProjectNotReadyError(f"只有暂停的项目才能继续，当前: {project.status.value}")
    # 关键：不删除任何 task，保留已完成步骤
    project.status = ProjectStatus.RUNNING
    await db.commit()
    # 重新触发流水线循环（循环会自动跳过 COMPLETED 的 task）
    from app.agents.orchestrator import orchestrator
    orchestrator._running_projects[project_id] = True
    route_result = await db.execute(
        select(__import__("app.database.models", fromlist=["ScienceQuestion"]))
    )
    model = "qwen-max"
    asyncio.create_task(orchestrator._execute_pipeline(project_id, user.id, model))
    return {"message": "已从断点继续", "project_id": project_id}"""

if "@router.post(\"/{project_id}/resume\")" in src:
    print("[跳过] resume 接口已存在")
elif anchor in src:
    src = src.replace(anchor, resume, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("[OK] 已添加 POST /projects/{id}/resume 接口（保留已完成步骤）")
else:
    print("[WARN] 锚点未匹配，请手动在 pause 接口后添加 resume")

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] OK")
except py_compile.PyCompileError as e:
    print("[syntax] L%d: %s" % (e.lineno, e.msg))
    if e.text:
        print("    " + repr(e.text[:110]))
