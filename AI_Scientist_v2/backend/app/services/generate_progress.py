"""课件生成作业进度（内存热路径 + 数据库低频镜像）

一次完整生成 = 大纲 1 次 LLM + 逐章 n 次 + 逐页配图 + 落库，要跑几十到上百秒，
前端每 1.2s 轮询真实进度。状态存两处：
- 内存 dict：轮询命中即返回，几乎不打数据库；主循环单线程 asyncio，读写原子不加锁。
- 数据库 generate_jobs 表：每次变更低频镜像一次，保证服务重启或超过内存 TTL 后仍能查到。

数据库写入永远包在 try 里：持久化失败只记日志，绝不影响生成主流程。
函数均为 async 且自开短会话，调用方无需传 db（作业主流程与请求级会话解耦）。
"""
import time
import uuid
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import update as sa_update, delete as sa_delete, select

logger = logging.getLogger(__name__)

TTL_SECONDS = 1800          # 内存作业保留时长
MAX_JOBS = 200              # 内存上限，防止无限增长
DB_RETENTION_DAYS = 7       # 数据库终态记录保留天数，启动时顺带清理

# 内存视图/数据库列共有的标量字段（result/error 只在终态写，避免大图反复落库）
_COLS = ("topic", "course_id", "course_title", "user_id", "status", "stage",
         "percent", "message", "chapters_done", "chapters_total",
         "slides_done", "slides_total")
# 返回给 API 的视图字段
_VIEW = ("status", "stage", "percent", "message", "chapters_done", "chapters_total",
         "slides_done", "slides_total", "result", "error", "topic",
         "course_id", "course_title")

_JOBS: dict[str, dict] = {}


def _session():
    from app.database.session import AsyncSessionLocal
    return AsyncSessionLocal()


def _gc() -> None:
    """回收过期内存作业（每次写入顺带做一次，成本可忽略）"""
    if len(_JOBS) <= MAX_JOBS:
        cutoff = time.time() - TTL_SECONDS
        for jid in [k for k, v in _JOBS.items() if v.get("updated_at", 0) < cutoff]:
            _JOBS.pop(jid, None)
        return
    for jid in list(_JOBS.keys())[: max(0, len(_JOBS) - MAX_JOBS)]:
        _JOBS.pop(jid, None)


async def new_job(**fields) -> str:
    """新建作业（内存 + 数据库各一条），返回 job_id"""
    job_id = uuid.uuid4().hex[:16]
    now = time.time()
    job = {
        "job_id": job_id,
        "status": "running",       # running / done / failed
        "stage": "queued",         # queued / material / outline / chapter / summary / render / persist / done
        "percent": 0,              # 0-100
        "message": "已排队，等待生成…",
        "chapters_done": 0,
        "chapters_total": 0,
        "slides_done": 0,
        "slides_total": 0,
        "result": None,
        "error": "",
        "created_at": now,
        "updated_at": now,
    }
    job.update(fields)
    _JOBS[job_id] = job
    _gc()
    await _db_write(job_id, job, terminal=False)
    return job_id


async def update(job_id: str, **fields) -> None:
    """更新作业：内存即时可见，数据库低频镜像。

    作业不在内存（服务重启后 / 已被回收）时仍把这次更新写进数据库，避免丢终态。
    """
    job = _JOBS.get(job_id)
    if job:
        job.update(fields)
        job["updated_at"] = time.time()
        _gc()
    else:
        job = {"job_id": job_id, **fields}
    await _db_write(job_id, job, terminal=fields.get("status") in ("done", "failed"))


async def _db_write(job_id: str, job: dict, terminal: bool) -> None:
    """把作业当前标量写库（有则更新、无则插入）；失败静默不影响生成。"""
    from app.database.models import GenerateJob
    try:
        vals = {c: job.get(c) for c in _COLS if job.get(c) is not None}
        if terminal:
            vals["result"] = job.get("result") or {}
            vals["error"] = job.get("error") or ""
        async with _session() as s:
            res = await s.execute(
                sa_update(GenerateJob).where(GenerateJob.job_id == job_id).values(**vals))
            if not res.rowcount:
                s.add(GenerateJob(job_id=job_id, **vals))
            await s.commit()
    except Exception as e:
        logger.debug(f"generate_job 持久化跳过 job={job_id}: {e}")


async def snapshot(job_id: str) -> dict | None:
    """给 API 的视图：先查内存；内存没有再回数据库（服务重启 / 超 TTL 后走这里）。"""
    job = _JOBS.get(job_id)
    if job:
        return {k: job.get(k) for k in _VIEW}
    from app.database.models import GenerateJob
    try:
        async with _session() as s:
            row = (await s.execute(
                select(GenerateJob).where(GenerateJob.job_id == job_id)
            )).scalar_one_or_none()
            if row is None:
                return None
            data = {k: getattr(row, k, None) for k in _VIEW}
            # 回填内存，后续轮询直接命中（result 空 dict 归一为 None 与内存态一致）
            _JOBS[job_id] = {"job_id": job_id, "created_at": time.time(),
                             "updated_at": time.time(), **data}
            return data
    except Exception as e:
        logger.debug(f"generate_job 读取失败 job={job_id}: {e}")
        return None


async def reconcile_on_startup() -> int:
    """服务启动：把上次进程遗留的 running 作业判为失败（后台任务已随进程消失），并清理过期终态。"""
    from app.database.models import GenerateJob
    try:
        async with _session() as s:
            res = await s.execute(
                sa_update(GenerateJob).where(GenerateJob.status == "running").values(
                    status="failed", stage="failed",
                    message="服务重启导致作业中断，可重新生成；已落库的课件仍可在「我生成过的课件」或课程页查看"))
            cutoff = datetime.now(timezone.utc) - timedelta(days=DB_RETENTION_DAYS)
            await s.execute(sa_delete(GenerateJob).where(GenerateJob.updated_at < cutoff))
            await s.commit()
            return res.rowcount or 0
        # 说明：updated_at 由 onupdate 触发，delete 不影响返回值
    except Exception as e:
        logger.warning(f"generate_job 启动对账跳过: {e}")
        return 0
