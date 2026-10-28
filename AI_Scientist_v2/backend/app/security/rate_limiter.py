"""智研星枢 - 滑动窗口速率限制器（Redis 分布式，无 Redis 自动回退内存）

真实上线姿势：限流状态放 Redis，多实例/多副本共享同一份计数；本机没 Redis 时回退到
进程内存（单实例依然有效）。对外 is_allowed / get_remaining 均为 async，调用方需 await。
"""
import time
import uuid
import logging
from collections import defaultdict
from typing import Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, max_requests: int = None, window_seconds: int = 60, bucket: str = "default"):
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = window_seconds
        self.bucket = bucket
        self._requests: dict[str, list[float]] = defaultdict(list)  # 内存回退

    def _rkey(self, key: str) -> str:
        return f"zhixing:rl:{self.bucket}:{key}"

    async def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        """返回 (是否放行, 拒绝时的建议等待秒数)。Redis 优先，异常/未启用回退内存。"""
        from app.services import redis_client

        r = redis_client.get_redis()
        if r is not None:
            try:
                return await self._redis_allowed(r, key)
            except Exception as e:  # 运行期 Redis 抖动：降级到内存，不影响放行判断
                logger.debug("限流 Redis 调用失败，回退内存：%s", e)
        return self._mem_allowed(key)

    async def _redis_allowed(self, r, key: str) -> Tuple[bool, Optional[int]]:
        now = time.time()
        window_start = now - self.window_seconds
        rk = self._rkey(key)
        member = f"{now:.6f}:{uuid.uuid4().hex}"
        pipe = r.pipeline(transaction=True)
        pipe.zremrangebyscore(rk, 0, window_start)   # 丢弃窗口外
        pipe.zcard(rk)                                # 当前窗口内计数
        pipe.zrange(rk, 0, 0, withscores=True)        # 最老一条（算 retry_after）
        pipe.zadd(rk, {member: now})
        pipe.expire(rk, int(self.window_seconds) + 1)
        _removed, count, oldest, _added, _exp = await pipe.execute()
        if count >= self.max_requests:
            # 刚多加的那条要撤掉，未放行的请求不计入
            await r.zrem(rk, member)
            oldest_ts = oldest[0][1] if oldest else now
            retry_after = int(oldest_ts + self.window_seconds - now) + 1
            return False, max(retry_after, 1)
        return True, None

    def _mem_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= self.max_requests:
            oldest = self._requests[key][0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            return False, max(retry_after, 1)
        self._requests[key].append(now)
        return True, None

    async def get_remaining(self, key: str) -> int:
        from app.services import redis_client

        r = redis_client.get_redis()
        if r is not None:
            try:
                rk = self._rkey(key)
                await r.zremrangebyscore(rk, 0, time.time() - self.window_seconds)
                count = await r.zcard(rk)
                return max(0, self.max_requests - int(count))
            except Exception as e:
                logger.debug("限流余量查询失败，回退内存：%s", e)
        now = time.time()
        window_start = now - self.window_seconds
        current = len([t for t in self._requests[key] if t > window_start])
        return max(0, self.max_requests - current)

    async def reset(self, key: str = None):
        from app.services import redis_client

        r = redis_client.get_redis()
        if r is not None and key:
            try:
                await r.delete(self._rkey(key))
            except Exception as e:
                logger.debug("限流重置失败：%s", e)
        if key:
            self._requests.pop(key, None)
        else:
            self._requests.clear()


rate_limiter = RateLimiter()
agent_rate_limiter = RateLimiter(max_requests=10, window_seconds=60, bucket="agent")
# 登录/注册专用：每 IP 每分钟最多 10 次，抵御撞库/暴力尝试与高频卡死
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60, bucket="auth")
