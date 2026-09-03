from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import Project
from app.api.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["团队配置"])

@router.put("/{project_id}/team")
async def update_team(project_id: str, config: dict,
                      db: AsyncSession = Depends(get_db),
                      user=Depends(get_current_user)):
    proj = (await db.execute(
        select(Project).where(Project.id == project_id)
    )).scalar_one_or_none()
    if not proj:
        raise HTTPException(404, "项目不存在")
    proj.team_config = config
    await db.commit()
    return {"ok": True, "team_config": config}

@router.get("/{project_id}/team")
async def get_team(project_id: str,
                   db: AsyncSession = Depends(get_db),
                   user=Depends(get_current_user)):
    proj = (await db.execute(
        select(Project).where(Project.id == project_id)
    )).scalar_one_or_none()
    if not proj:
        raise HTTPException(404, "项目不存在")
    return {"team_config": proj.team_config or {}}
