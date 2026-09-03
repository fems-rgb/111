p = "backend/app/api/v1/projects.py"
src = open(p, encoding="utf-8").read()

# 检查是否已有正确的 resume 接口
has_resume = "@router.post(\"/{project_id}/resume\")" in src
has_correct = "resume_mode=True" in src

print("当前状态:")
print("  has resume route:", has_resume)
print("  has resume_mode=True:", has_correct)

if has_resume and has_correct:
    print("\n[跳过] resume 接口已存在且正确")
else:
    # 在 pause 接口之后插入（在 restart 之前）
    # 找到 pause 接口的 return 行
    lines = src.split("\n")
    insert_at = None
    for i, l in enumerate(lines):
        if 'return {"message": "项目已暂停"}' in l:
            insert_at = i + 1  # 在 return 行之后插入
            break

    if insert_at is None:
        print("\n[WARN] 未找到 pause 接口的 return 行")
    else:
        resume_code = '''
@router.post("/{project_id}/resume")
async def resume(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """从暂停处继续：保留已完成的步骤，从下一个 pending 步骤接着跑"""
    from app.core.exceptions import ProjectNotReadyError
    project = await _get_project(db, project_id, user.id)
    if project.status == ProjectStatus.RUNNING:
        return {"message": "项目已在运行中"}
    if project.status != ProjectStatus.PAUSED:
        raise ProjectNotReadyError(f"只有暂停的项目才能继续，当前: {project.status.value}")
    # resume_mode=True -> 不删 task，复用现有，从断点继续
    await orchestrator.start_project(db, project_id, user.id, resume_mode=True)
    return {"message": "已从断点继续", "project_id": project_id}

'''
        lines.insert(insert_at, resume_code.rstrip("\n"))
        src = "\n".join(lines)
        open(p, "w", encoding="utf-8").write(src)
        print("\n[OK] 已添加 resume 接口（调用 start_project resume_mode=True）")

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] projects.py OK")
except py_compile.PyCompileError as e:
    print("[syntax] L%d: %s" % (e.lineno, e.msg))
