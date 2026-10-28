"""智研星枢 - 登录失败锁定（按账号维度，抵御撞库/暴力破解）

与 rate_limiter（按 IP）互补：这里针对具体用户名，一段时间内累计失败达到阈值即临时
锁定该账号登录，返回 429 + Retry-After；成功登录或锁定到期则自动解除。

真实上线姿势：计数与锁定标记放 Redis（TTL 自动过期），多实例共享；本机无 Redis 时
回退进程内存。对外方法均为 async，调用方需 await。
"""
import time
import logging
from collections import defaultdict
from typing import Tuple

logger = logging.getLogger(__name__)


class LoginGuard:
    def __init__(self, max_fails: int = 5, window_seconds: int = 900, lock_seconds: int = 900):
        self.max_fails = max_fails          # 触发锁定的连续失败次数
        self.window_seconds = window_seconds  # 失败计数窗口（秒）
        self.lock_seconds = lock_seconds      # 锁定时长（秒）
        self._fails: dict[str, list[float]] = defaultdict(list)  # 内存回退
        self._locked_until: dict[str, float] = {}

    @staticmethod
    def _norm(key: str) -> str:
        return (key or "").strip().lower()

    def _fails_key(self, k: str) -> str:
        return f"zhixing:loginfails:{k}"

    def _lock_key(self, k: str) -> str:
        return f"zhixing:loginlock:{k}"

    def _redis(self):
        from app.services import redis_client
        return redis_client.get_redis()

    async def is_locked(self, key: str) -> Tuple[bool, int]:
        """当前是否处于锁定；返回 (locked, 剩余秒数)"""
        k = self._norm(key)
        r = self._redis()
        if r is not None:
            try:
                ttl = await r.ttl(self._lock_key(k))
                if ttl and ttl > 0:
                    return True, int(ttl)
                return False, 0
            except Exception as e:
                logger.debug("登录锁定查询 Redis 失败，回退内存：%s", e)
        until = self._locked_until.get(k, 0.0)
        now = time.time()
        if until > now:
            return True, int(until - now) + 1
        if k in self._locked_until:
            self._locked_until.pop(k, None)
        return False, 0

    async def record_fail(self, key: str) -> Tuple[bool, int]:
        """记录一次失败；达到阈值则进入锁定并返回 (True, 锁定秒数)"""
        k = self._norm(key)
        r = self._redis()
        if r is not None:
            try:
                fk = self._fails_key(k)
                cnt = await r.incr(fk)
                if cnt == 1:
                    await r.expire(fk, self.window_seconds)
                if cnt >= self.max_fails:
                    await r.setex(self._lock_key(k), self.lock_seconds, "1")
                    await r.delete(fk)
                    return True, self.lock_seconds
                return False, 0
            except Exception as e:
                logger.debug("登录失败计数 Redis 失败，回退内存：%s", e)
        now = time.time()
        start = now - self.window_seconds
        self._fails[k] = [t for t in self._fails[k] if t > start]
        self._fails[k].append(now)
        if len(self._fails[k]) >= self.max_fails:
            self._locked_until[k] = now + self.lock_seconds
            self._fails[k].clear()
            return True, self.lock_seconds
        return False, 0

    async def reset(self, key: str) -> None:
        """登录成功后清除该账号的失败与锁定记录"""
        k = self._norm(key)
        r = self._redis()
        if r is not None:
            try:
                await r.delete(self._fails_key(k), self._lock_key(k))
            except Exception as e:
                logger.debug("登录锁定重置 Redis 失败：%s", e)
        self._fails.pop(k, None)
        self._locked_until.pop(k, None)

    async def clear(self) -> None:
        """清空内存态（主要供测试）。Redis 模式靠 TTL 自然过期，不做全量清扫。"""
        self._fails.clear()
        self._locked_until.clear()


login_guard = LoginGuard()
