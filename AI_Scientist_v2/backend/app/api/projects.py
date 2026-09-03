"""项目与流水线API路由"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.api.deps import get_current_user, check_rate_limit
from app.database.models import User
from app.agents.orchestrator import orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


class StartProjectRequest(BaseModel):
    research_question: str = Field(..., min_length=10, max_length=2000)
    custom_pipeline: list[str] | None = None
    mode: str = Field(default="quick", pattern="^(quick|expert)$")


class ReviewDecision(BaseModel):
    approved: bool
    comment: str = ""


@router.post("/start")
async def start_project(
    req: StartProjectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rate: None = Depends(check_rate_limit),
):
    """启动研究项目流水线"""
    try:
        result = await orchestrator.start_project(
            db=db, project_id=None, user_id=user.id,
            custom_pipeline=req.custom_pipeline, mode=req.mode,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Start project failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.get("/{project_id}/status")
async def get_project_status(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目状态与进度"""
    from sqlalchemy import select
    from app.database.models import Project, AgentTask
    proj = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="项目不存在")
    tasks = (await db.execute(
        select(AgentTask).where(AgentTask.project_id == project_id).order_by(AgentTask.step_order)
    )).scalars().all()
    return {
        "project": {"id": proj.id, "status": proj.status.value, "complexity": proj.complexity.value if proj.complexity else None},
        "tasks": [{"id": t.id, "agent": t.agent_name, "step": t.step_order, "status": t.status.value} for t in tasks],
    }


@router.post("/{project_id}/pause")
async def pause_project(project_id: int, user: User = Depends(get_current_user)):
    orchestrator.pause_project(project_id)
    return {"success": True, "message": "已暂停"}


@router.post("/review/{task_id}")
async def submit_review(
    task_id: int, decision: ReviewDecision,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交人工审核决定"""
    try:
        result = await orchestrator.resume_from_review(
            db=db, task_id=task_id, user_id=user.id,
            comment=decision.comment, approved=decision.approved,
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
