from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.session import get_db
from app.database.models import User, Project, AuditLog
from app.schemas.auth import UserInfo
from app.api.deps import require_admin
from app.observability.cost_tracker import cost_tracker
from app.security.prompt_guard import prompt_guard

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.get("/stats")
async def system_stats(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    project_count = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    return {"user_count": user_count, "project_count": project_count,
            "cost_summary": cost_tracker.get_summary(), "prompt_guard": prompt_guard.get_stats()}


@router.get("/users", response_model=list[UserInfo])
async def list_users(limit: int = 50, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    return [UserInfo.model_validate(u) for u in result.scalars().all()]


@router.post("/users/{user_id}/toggle")
async def toggle_user(user_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        return {"error": "用户不存在"}
    target.is_active = not target.is_active
    await db.commit()
    return {"message": f"用户 {target.username} 已{'启用' if target.is_active else '禁用'}"}