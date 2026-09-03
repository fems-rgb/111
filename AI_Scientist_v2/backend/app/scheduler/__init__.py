from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.models import Pipeline
import logging, asyncio

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

async def _scheduled_run(pipeline_id: str):
    async with AsyncSessionLocal() as db:
        p = await db.get(Pipeline, pipeline_id)
        if not p or p.status != "active":
            return
        from app.api.v1.automation import _execute_pipeline
        await _execute_pipeline(p, db)
        logger.info(f"[Scheduler] Pipeline {pipeline_id} executed")

def register_pipeline_jobs():
    async def _load():
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(
                select(Pipeline).where(Pipeline.trigger == "cron")
            )).scalars().all()
            for p in rows:
                if p.schedule_cron:
                    scheduler.add_job(
                        _scheduled_run,
                        CronTrigger.from_crontab(p.schedule_cron),
                        args=[p.id], id=f"pipeline_{p.id}", replace_existing=True,
                    )
                    logger.info(f"[Scheduler] Registered {p.id}: {p.schedule_cron}")
    scheduler.start()
    asyncio.ensure_future(_load())

def reload_pipeline_job(pipeline_id: str, cron_expr: str | None):
    job_id = f"pipeline_{pipeline_id}"
    if cron_expr:
        scheduler.add_job(_scheduled_run, CronTrigger.from_crontab(cron_expr),
                          args=[pipeline_id], id=job_id, replace_existing=True)
    else:
        try: scheduler.remove_job(job_id)
        except Exception: pass
