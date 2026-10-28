"""智研星枢 - 课件生成后台作业队列（削峰 + 并发闸 + 背压）

为什么需要它：一次课件生成要跑几十到上百秒、且烧 LLM 配额。原实现是「每个请求
asyncio.create_task 直接开跑」，几十人同时点就会把进程与模型限流一起打爆。真实网站
的做法是把重活交给**固定 worker 池 + 有界队列**：请求先入队拿 job_id，worker 按上限逐个
取出执行；队列排满时对新请求直接返回 429（背压/削峰），而不是无限堆积拖死服务。

并发控制两层：
- 单实例：worker 数 = GENERATION_MAX_CONCURRENCY，天然限制本地同时执行数。
- 多实例（接了 Redis 时）：额外用「租约 ZSET」做集群级并发闸，job_id 作为成员、到期时间戳
  作为分数；进程崩溃时租约自然过期被回收，不会永久占坑。无 Redis 时跳过，仅靠单实例 worker 数。

降级原则：Redis 相关操作全部 try/except，任何异常都退回「本地直接执行」，绝不影响主流程。
"""
from __future__ import annotations

import asyncio
import time
import logging
from typing import Awaitable, Callable, Optional, Tuple

from app.config import settings
from app.services import redis_client

logger = logging.getLogger(__name__)

# 集群级并发闸：成员=job_id，分数=租约到期时间戳（秒）
_ACTIVE_ZSET = "zhixing:gen:active"
_LEASE_SECONDS = 1800        # 单个作业最长占坑时间（远超正常生成时长，用于崩溃自愈）
_SLOT_POLL_SECONDS = 1.0     # 等全局空位时的轮询间隔
_MAX_WAIT_SECONDS = 3600     # 排队等待全局空位的硬上限，超时判失败


class GenerationQueue:
    def __init__(self) -> None:
        self._n = max(1, int(settings.GENERATION_MAX_CONCURRENCY))
        self._qmax = max(self._n, int(settings.GENERATION_QUEUE_MAX))
        self._queue: Optional[asyncio.Queue] = None
        self._workers: list[asyncio.Task] = []
        self._local_active = 0
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        self._queue = asyncio.Queue(maxsize=self._qmax)
        self._workers = [asyncio.create_task(self._worker(i), name=f"gen-worker-{i}")
                         for i in range(self._n)]
        self._started = True
        logger.info("🚦 课件生成队列已启动：worker=%d，等待队列上限=%d", self._n, self._qmax)

    async def stop(self) -> None:
        for w in self._workers:
            w.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers = []
        self._started = False
        self._queue = None

    def stats(self) -> dict:
        queued = self._queue.qsize() if self._queue else 0
        return {"started": self._started, "queued": queued, "local_active": self._local_active,
                "workers": self._n, "queue_max": self._qmax,
                "distributed_gate": redis_client.redis_enabled()}

    def has_capacity(self) -> Tuple[bool, int]:
        """入队前预检：等待队列是否还有位置。返回 (是否可接受, 当前排队数)。"""
        if self._queue is None:
            return True, 0
        q = self._queue.qsize()
        return q < self._qmax, q

    async def submit(self, job_id: str, factory: Callable[[], Awaitable[None]]) -> None:
        """把作业放入队列。未启动则即时懒启动（便于脚本/测试）。队列满抛 asyncio.QueueFull。"""
        if not self._started or self._queue is None:
            await self.start()
        self._queue.put_nowait((job_id, factory))  # 满 → QueueFull，由调用方转 429

    async def _worker(self, idx: int) -> None:
        while True:
            job_id, factory = await self._queue.get()
            try:
                ok = await self._acquire_global_slot(job_id)
                if not ok:
                    await self._fail_overwait(job_id)
                    continue
                self._local_active += 1
                try:
                    await factory()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("生成 worker 执行异常 job=%s", job_id)
                finally:
                    self._local_active -= 1
                    await self._release_global_slot(job_id)
            finally:
                self._queue.task_done()

    async def _fail_overwait(self, job_id: str) -> None:
        """等待全局空位超时：把作业判失败，避免用户无限等待。"""
        logger.warning("生成作业等待全局并发位超时 job=%s", job_id)
        try:
            from app.services import generate_progress as gp
            await gp.update(job_id, status="failed", stage="failed",
                            message="系统繁忙：生成队列长时间已满，请稍后重试",
                            error="global slot wait timeout")
        except Exception as e:
            logger.debug("标记超时失败态出错 job=%s: %s", job_id, e)

    async def _acquire_global_slot(self, job_id: str) -> bool:
        """集群级并发闸。无 Redis → 直接放行（靠单实例 worker 数限并发）。有 Redis → 租约占坑。"""
        r = redis_client.get_redis()
        if r is None:
            return True
        deadline = time.time() + _MAX_WAIT_SECONDS
        try:
            while True:
                now = time.time()
                pipe = r.pipeline(transaction=True)
                pipe.zremrangebyscore(_ACTIVE_ZSET, 0, now)      # 回收过期租约（崩溃自愈）
                pipe.zcard(_ACTIVE_ZSET)                          # 当前活跃数
                _removed, active = await pipe.execute()
                active = int(active)
                if active < self._n:
                    await r.zadd(_ACTIVE_ZSET, {job_id: now + _LEASE_SECONDS})
                    return True
                if time.time() > deadline:
                    return False
                await asyncio.sleep(_SLOT_POLL_SECONDS)
        except Exception as e:
            logger.debug("全局并发闸 Redis 异常，降级为本地放行：%s", e)
            return True

    async def _release_global_slot(self, job_id: str) -> None:
        r = redis_client.get_redis()
        if r is None:
            return
        try:
            await r.zrem(_ACTIVE_ZSET, job_id)
        except Exception as e:
            logger.debug("释放全局并发位失败 job=%s: %s", job_id, e)


generation_queue = GenerationQueue()
