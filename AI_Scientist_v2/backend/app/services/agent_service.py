from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import AgentTask
import logging

logger = logging.getLogger(__name__)


async def get_project_tasks(db: AsyncSession, project_id: int) -> list:
    result = await db.execute(select(AgentTask).where(AgentTask.project_id == project_id).order_by(AgentTask.step_order))
    return result.scalars().all()


async def get_task_detail(db: AsyncSession, task_id: int) -> AgentTask:
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise ValueError("任务不存在")
    return task