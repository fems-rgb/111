"""智研星枢 - SSE实时事件流（Agent进度/通知/状态变更）"""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.database.models import User
from app.api.deps import get_current_user_flexible
from app.core.events import event_bus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stream", tags=["实时推送"])

# 每个用户的SSE队列
_user_queues: dict[int, list[asyncio.Queue]] = {}


async def _event_handler(data: dict = None, **kwargs):
    """事件总线处理器：将事件分发到所有在线用户的SSE队列。
    兼容两种调用：emit(dict) 时 data={...}；emit(**kwargs) 时走 kwargs。
    """
    if isinstance(data, dict) and data:
        payload = data
    elif kwargs:
        payload = kwargs
    else:
        payload = {}
    user_id = payload.get("user_id")
    for uid, queues in _user_queues.items():
        if user_id is None or uid == user_id:
            for q in queues:
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    pass



@router.get("/events")
async def sse_events(request: Request, user: User = Depends(get_current_user_flexible)):
    """SSE端点：前端通过EventSource连接"""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    if user.id not in _user_queues:
        _user_queues[user.id] = []
    _user_queues[user.id].append(queue)
    logger.info(f"SSE连接建立: user={user.id}")

    async def generator():
        try:
            # 发送初始心跳
            yield f"data: {json.dumps({'type': 'connected', 'user_id': user.id})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
                except asyncio.TimeoutError:
                    # 心跳保活
                    yield f": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if user.id in _user_queues:
                _user_queues[user.id] = [q for q in _user_queues[user.id] if q is not queue]
                if not _user_queues[user.id]:
                    del _user_queues[user.id]
            logger.info(f"SSE连接断开: user={user.id}")

    return StreamingResponse(generator(), media_type="text/event-stream; charset=utf-8",
                           headers={"Cache-Control": "no-cache", "Connection": "keep-alive",
                                    "X-Accel-Buffering": "no"})