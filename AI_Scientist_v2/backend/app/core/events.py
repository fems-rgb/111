"""智研星枢 - 事件总线（解耦模块间通信）"""
import asyncio
import logging
from typing import Callable, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """
    进程内事件总线。
    支持：同步/异步订阅、一次性监听、广播。
    用途：Agent完成→通知用户、成本超阈值→告警等场景。
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._once_handlers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, handler: Callable):
        """订阅事件"""
        self._handlers[event].append(handler)
        logger.debug(f"事件订阅: {event} -> {handler.__name__}")

    def once(self, event: str, handler: Callable):
        """一次性订阅"""
        self._once_handlers[event].append(handler)

    def off(self, event: str, handler: Callable = None):
        """取消订阅"""
        if handler:
            self._handlers[event] = [h for h in self._handlers[event] if h != handler]
        else:
            self._handlers[event] = []

    async def emit(self, event: str, data: Any = None, **kwargs):
        """广播事件。data 可以是 dict，会自动解包为关键字参数传给 handler"""
        all_handlers = list(self._handlers.get(event, []))
        once = self._once_handlers.pop(event, [])
        all_handlers.extend(once)

        for handler in all_handlers:
            try:
                # 智能传参：如果 data 是 dict 且 handler 接受关键字参数，则解包
                call_kwargs = {}
                if isinstance(data, dict):
                    call_kwargs = data
                if asyncio.iscoroutinefunction(handler):
                    if call_kwargs:
                        await handler(**call_kwargs)
                    else:
                        await handler(data)
                else:
                    if call_kwargs:
                        handler(**call_kwargs)
                    else:
                        handler(data)
            except Exception as e:
                logger.error(f"事件处理器 {handler.__name__} 异常: {e}", exc_info=True)


# 全局事件总线单例
event_bus = EventBus()

# ── 预定义事件名 ──
class Events:
    PROJECT_CREATED = "project.created"
    PROJECT_COMPLETED = "project.completed"
    PROJECT_FAILED = "project.failed"
    AGENT_STARTED = "agent.started"
    AGENT_STEP_UPDATE = "agent.step_update"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_REVIEW_NEEDED = "agent.review_needed"
    COST_THRESHOLD = "cost.threshold_exceeded"
    USER_REGISTERED = "user.registered"
    SYSTEM_ERROR = "system.error"