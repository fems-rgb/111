"""课件生成作业进度表（进程内）

为什么用它：整套课件生成 = 大纲 1 次 LLM + 逐章 n 次 LLM + 逐页配图 + 落库，
一次请求要跑几十到上百秒。若不同步阻塞 HTTP，就需要一个地方让前端轮询真实进度。
数据只保留 30 分钟（完成后同样回收），因此放内存即可，无需建表；
主循环是单线程 asyncio，dict 读写本身原子，不加锁。
"""
import time
import uuid
import logging

logger = logging.getLogger(__name__)

TTL_SECONDS = 1800          # 作业记录保留时长
MAX_JOBS = 200              # 上限，防止长时间运行后内存无限增长

_JOBS: dict[str, dict] = {}


def _gc() -> None:
    """回收过期作业（每次写入时顺带做一次，成本可忽略）"""
    if len(_JOBS) <= MAX_JOBS:
        cutoff = time.time() - TTL_SECONDS
        for jid in [k for k, v in _JOBS.items() if v.get("updated_at", 0) < cutoff]:
            _JOBS.pop(jid, None)
        return
    for jid in list(_JOBS.keys())[: max(0, len(_JOBS) - MAX_JOBS)]:
        _JOBS.pop(jid, None)


def new_job(**fields) -> str:
    """新建作业，返回 job_id"""
    job_id = uuid.uuid4().hex[:16]
    now = time.time()
    _JOBS[job_id] = {
        "job_id": job_id,
        "status": "running",       # running / done / failed
        "stage": "queued",         # queued / material / outline / chapter / render / persist / done
        "percent": 0,              # 0-100
        "message": "已排队，等待生成…",
        "chapters_done": 0,
        "chapters_total": 0,
        "slides_done": 0,
        "slides_total": 0,
        "result": None,            # 完成后放 _build_deck 的返回值
        "error": "",
        "created_at": now,
        "updated_at": now,
    }
    _JOBS[job_id].update(fields)
    _gc()
    return job_id


def update(job_id: str, **fields) -> None:
    """更新作业字段（作业不存在时静默忽略，避免后台任务与请求竞态报错）"""
    job = _JOBS.get(job_id)
    if not job:
        return
    job.update(fields)
    job["updated_at"] = time.time()
    _gc()


def get(job_id: str) -> dict | None:
    return _JOBS.get(job_id)


def snapshot(job_id: str) -> dict | None:
    """给 API 的视图：去掉内部时间戳，附带存活标记"""
    job = _JOBS.get(job_id)
    if not job:
        return None
    return {k: v for k, v in job.items() if not k.endswith("_at")}
