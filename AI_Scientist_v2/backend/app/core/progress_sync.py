"""
自动进度同步器（对齐 README 二十六章 P0-1 修复）

行为：
1. 每 5 秒扫描所有 running 的题库任务
2. 按关联 project 的 agent_tasks 完成比例，写回 question_tasks.progress
3. **运行中 progress 上限 95**：progress=100 与 status=completed 必须原子绑定
   （completed 由 pipeline 回写文档成功分支设置，本同步器不会主动置 100）
4. **僵尸兑底**：running 且已 5 min+ 未更新且关联 project 全 completed 但
   document_path 仍为空 → 标 failed + 明确 error_message，避免前端卡在 100%
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.database.models import QuestionTask, ScienceQuestion, Project, AgentTask

log = logging.getLogger(__name__)
_task = None

# progress 运行上限，防止"100% 但未生成完"（README P0-1）
RUNNING_PROGRESS_CAP = 95
# 僵尸判定：project 全完成但 document_path 空 + 超过此时长即 failed
ZOMBIE_GRACE_MINUTES = 5

_COMPLETED_TOKENS = {"COMPLETED"}


def _is_completed(status) -> bool:
    return str(getattr(status, "value", status)).strip().upper() in _COMPLETED_TOKENS


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
                done = sum(1 for (s,) in rows if _is_completed(s))
                raw = round(done / total * 100)

                # [P0-1] 运行中硬上限 95
                progress = min(raw, RUNNING_PROGRESS_CAP)

                if task.progress != progress:
                    task.progress = progress
                    log.info("[progress] task=%s -> %s%% (raw=%s)", task.id, progress, raw)

                # [P0-1] 僵尸兑底：agent 全完成但文档仍未回写
                if (
                    done == total
                    and not task.document_path
                    and task.started_at
                    and datetime.now(timezone.utc) - (
                        task.started_at if task.started_at.tzinfo
                        else task.started_at.replace(tzinfo=timezone.utc)
                    ) > timedelta(minutes=ZOMBIE_GRACE_MINUTES)
                ):
                    task.status = "failed"
                    task.error_message = (
                        f"僵尸任务：Agent 已全部完成但 {ZOMBIE_GRACE_MINUTES} 分钟内未回写文档，"
                        "已自动终止；请重试或查看 Orchestrator 日志"
                    )
                    task.completed_at = datetime.now(timezone.utc)
                    log.warning("[progress] task=%s 判定为僵尸 -> failed", task.id)

            except Exception as e:
                log.debug("[progress] skip task=%s: %s", getattr(task, "id", "?"), e)
        await db.commit()

        # 顺带把成本内存日桶低频镜像到 cost_daily（预测/预警数据源；内部限流 >=60s）
        try:
            from app.services.prediction import flush_cost_daily
            await flush_cost_daily(db)
        except Exception as e:
            log.debug("[progress] cost daily flush skip: %s", e)


async def _loop():
    await asyncio.sleep(5)
    while True:
        try:
            await _sync_once()
        except Exception as e:
            log.warning("[progress] sync error: %s", e, exc_info=True)
        await asyncio.sleep(5)


def start_progress_sync():
    """在 FastAPI lifespan 启动时调用一次"""
    global _task
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop())
        log.info("[progress] 自动进度同步已启动 (间隔 5s，运行上限 %s%%)", RUNNING_PROGRESS_CAP)


def stop_progress_sync():
    global _task
    if _task and not _task.done():
        _task.cancel()
