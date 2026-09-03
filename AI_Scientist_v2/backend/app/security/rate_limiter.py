"""智研星枢 - 滑动窗口速率限制器"""
import time
import logging
from collections import defaultdict
from typing import Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, max_requests: int = None, window_seconds: int = 60):
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, Optional[int]]:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= self.max_requests:
            oldest = self._requests[key][0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            return False, max(retry_after, 1)
        self._requests[key].append(now)
        return True, None

    def get_remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        current = len([t for t in self._requests[key] if t > window_start])
        return max(0, self.max_requests - current)

    def reset(self, key: str = None):
        if key:
            self._requests.pop(key, None)
        else:
            self._requests.clear()


rate_limiter = RateLimiter()
agent_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)