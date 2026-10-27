"""智研星枢 - 登录失败锁定（按账号维度，抵御撞库/暴力破解）

与 rate_limiter（按 IP）互补：这里针对具体用户名，一段时间内累计失败达到阈值
即临时锁定该账号登录，返回 429 + Retry-After；成功登录或锁定到期则自动解除。

内存态实现（进程重启即清零），与项目现有滑动窗口限流器风格一致；如需跨重启持久
可改为在 users 表加 failed_attempts/locked_until 列，但 SQLite 需配套 ALTER 迁移。
"""
import time
from collections import defaultdict
from typing import Tuple


class LoginGuard:
    def __init__(self, max_fails: int = 5, window_seconds: int = 900, lock_seconds: int = 900):
        self.max_fails = max_fails          # 触发锁定的连续失败次数
        self.window_seconds = window_seconds  # 失败计数窗口（秒）
        self.lock_seconds = lock_seconds      # 锁定时长（秒）
        self._fails: dict[str, list[float]] = defaultdict(list)
        self._locked_until: dict[str, float] = {}

    @staticmethod
    def _norm(key: str) -> str:
        return (key or "").strip().lower()

    def is_locked(self, key: str) -> Tuple[bool, int]:
        """当前是否处于锁定；返回 (locked, 剩余秒数)"""
        k = self._norm(key)
        until = self._locked_until.get(k, 0.0)
        now = time.time()
        if until > now:
            return True, int(until - now) + 1
        # 到期即清理
        if k in self._locked_until:
            self._locked_until.pop(k, None)
        return False, 0

    def record_fail(self, key: str) -> Tuple[bool, int]:
        """记录一次失败；达到阈值则进入锁定并返回 (True, 锁定秒数)"""
        k = self._norm(key)
        now = time.time()
        start = now - self.window_seconds
        self._fails[k] = [t for t in self._fails[k] if t > start]
        self._fails[k].append(now)
        if len(self._fails[k]) >= self.max_fails:
            self._locked_until[k] = now + self.lock_seconds
            self._fails[k].clear()
            return True, self.lock_seconds
        return False, 0

    def reset(self, key: str) -> None:
        """登录成功后清除该账号的失败与锁定记录"""
        k = self._norm(key)
        self._fails.pop(k, None)
        self._locked_until.pop(k, None)

    def clear(self) -> None:
        self._fails.clear()
        self._locked_until.clear()


login_guard = LoginGuard()
