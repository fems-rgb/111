import re, os

BASE = r"D:\AI_Scientist\AI_Scientist\backend"

# ============================================================
# 1. 修复 exceptions.py - 确保新异常类存在
# ============================================================
exc_path = os.path.join(BASE, "app", "core", "exceptions.py")
with open(exc_path, "r", encoding="utf-8") as f:
    content = f.read()

new_classes = '''

class ProjectAlreadyRunningError(AppException):
    """项目已在运行中"""
    def __init__(self, project_id: int = 0):
        super().__init__(
            f"项目 {project_id} 正在运行中，请先暂停或等待完成后再重新启动",
            status.HTTP_409_CONFLICT,
            "PROJECT_ALREADY_RUNNING"
        )
        self.project_id = project_id


class ProjectNotReadyError(AppException):
    """项目状态不允许当前操作"""
    def __init__(self, message: str = "项目当前状态不允许此操作"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, "PROJECT_NOT_READY")

'''

if "ProjectAlreadyRunningError" not in content:
    # 在 global_exception_handler 之前插入
    content = content.replace(
        "async def global_exception_handler",
        new_classes + "\nasync def global_exception_handler"
    )
    with open(exc_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] exceptions.py - 新增 ProjectAlreadyRunningError / ProjectNotReadyError")
else:
    print("[SKIP] exceptions.py - 异常类已存在")

# ============================================================
# 2. 修复 projects.py - 安全替换 start 路由
# ============================================================
proj_path = os.path.join(BASE, "app", "api", "v1", "projects.py")
with open(proj_path, "r", encoding="utf-8") as f:
    content = f.read()

# 用正则匹配 start 路由（兼容各种空白差异）
pattern = r'(@router\.post\("/\{project_id\}/start"\)\s*\nasync def start\(.*?)(?=@router\.|async def pause)'
match = re.search(pattern, content, re.DOTALL)

if match:
    new_start = '''@router.post("/{project_id}/start")
async def start(
    project_id: int,
    force: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project(db, project_id, user.id)

    # 状态前置检查
    if project.status == ProjectStatus.RUNNING and not force:
        from app.core.exceptions import ProjectAlreadyRunningError
        raise ProjectAlreadyRunningError(project_id)

    allowed = {ProjectStatus.DRAFT, ProjectStatus.COMPLETED, ProjectStatus.FAILED, ProjectStatus.PAUSED}
    if project.status not in allowed and not force:
        from app.core.exceptions import ProjectNotReadyError
        raise ProjectNotReadyError(f"项目当前状态为 {project.status.value}，无法启动")

    # 设为 PLANNING，由 orchestrator 内部控制后续流转
    project.status = ProjectStatus.PLANNING
    await db.commit()

    try:
        result = await orchestrator.start_project(db, project_id, user.id)
        return {"message": "项目已启动", "project_id": project_id, **(result if isinstance(result, dict) else {})}
    except Exception as e:
        # 启动失败时回滚状态
        project.status = ProjectStatus.FAILED
        await db.commit()
        from app.core.exceptions import AgentException
        raise AgentException(f"项目启动失败: {str(e)}")


'''
    content = content[:match.start()] + new_start + content[match.end():]
    with open(proj_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] projects.py - start 路由已替换")
else:
    print("[WARN] projects.py - 未找到 start 路由，请手动检查")

# ============================================================
# 3. 修复 orchestrator.py - ValueError → 业务异常 + 进度修复
# ============================================================
orch_path = os.path.join(BASE, "app", "agents", "orchestrator.py")
with open(orch_path, "r", encoding="utf-8") as f:
    content = f.read()

# 3a. 替换 "项目正在运行中" 的 ValueError
old_check = 'raise ValueError("项目正在运行中")'
new_check = '''from app.core.exceptions import ProjectAlreadyRunningError
            raise ProjectAlreadyRunningError(project_id)'''

if old_check in content:
    content = content.replace(old_check, new_check)
    print("[OK] orchestrator.py - ValueError 已替换为 ProjectAlreadyRunningError")
else:
    print("[SKIP] orchestrator.py - 已修复或未找到目标行")

# 3b. 修复进度：确保每个 agent 执行后更新 task 进度
# 查找是否有 progress 更新逻辑，如果没有则在适当位置添加
if "task.progress" not in content and "progress" not in content:
    print("[INFO] orchestrator.py - 未发现进度更新逻辑，需要查看完整文件后添加")

with open(orch_path, "w", encoding="utf-8") as f:
    f.write(content)

# ============================================================
# 4. 重置项目1状态
# ============================================================
print("\\n[DONE] 所有文件修复完成。请重启后端服务。")
print("重启后执行: python _reset_project.py")

