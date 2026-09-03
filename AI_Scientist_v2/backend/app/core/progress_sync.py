"""
自动进度同步器（极简版）
- 每 5 秒扫描所有 running 的题库任务
- 按关联 project 的 agent_tasks 完成比例，把真实进度写回 question_tasks.progress
- 前端轮询 get_task_status 读取该字段，自动刷新 → 与工作台同步、动态
"""
import asyncio
import logging
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.models import QuestionTask, ScienceQuestion, Project, AgentTask

log = logging.getLogger(__name__)
_task = None


async def _sync_once():
    async with AsyncSessionLocal() as db:
        tasks = (await db.execute(
            select(QuestionTask).where(QuestionTask.status == "running")
        )).scalars().all()
        for task in tasks:
            try:
                sq = (await db.execute(
                    select(ScienceQuestion).where(ScienceQuestion.question_id == task.question_id)
                )).scalar_one_or_none()
                if not sq or not sq.title:
                    continue
                key = str(sq.title).strip()[:20]
                proj = (await db.execute(
                    select(Project).where(Project.title.like("%" + key + "%"))
                )).scalars().first()
                if not proj:
                    continue
                rows = (await db.execute(
                    select(AgentTask.status).where(AgentTask.project_id == proj.id)
                )).all()
                total = len(rows)
                if not total:
                    continue
                done = sum(
                    1 for (s,) in rows
                    if str(getattr(s, "value", s)).strip().upper() == "COMPLETED"
                )
                progress = round(done / total * 100)
                if task.progress != progress:
                    task.progress = progress
                    log.info("[progress] task=%s -> %s%%", task.id, progress)
            except Exception as e:
                log.debug("[progress] skip task=%s: %s", task.id, e)
        await db.commit()


async def _loop():
    await asyncio.sleep(5)
    while True:
        try:
            await _sync_once()
        except Exception as e:
            log.warning("[progress] sync error: %s", e)
        await asyncio.sleep(5)


def start_progress_sync():
    """在 FastAPI lifespan 启动时调用一次"""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())
        log.info("[progress] 自动进度同步已启动 (间隔 5s)")


def stop_progress_sync():
    global _task
    if _task and not _task.done():
        _task.cancel()