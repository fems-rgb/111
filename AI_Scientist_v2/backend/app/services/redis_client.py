"""智研星枢 - Redis 异步客户端（可选依赖，全部优雅降级）

定位：把限流、登录锁定、生成并发闸等「进程内状态」升级为「多实例共享」的分布式状态。
真实上线姿势与市面应用一致 —— 单机用内存、横向扩展时接 Redis。

设计约束（务必保持）：
- REDIS_URL 留空、redis 包未装、或运行时连接失败，一律返回「不可用」，调用方自动回退内存实现，
  主流程绝不因 Redis 缺失而报错。因此本机不装 Redis 也能照常跑。
- 懒初始化：首次访问才建连接，避免 import 期就依赖 redis。
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Any] = None
_state = "uninit"  # uninit / off / on / error


def _init() -> None:
    """惰性建立客户端；任何失败都记为不可用（不抛）。"""
    global _client, _state
    if _state != "uninit":
        return
    url = (settings.REDIS_URL or "").strip()
    if not url:
        _state = "off"
        logger.info("Redis 未配置（REDIS_URL 为空），限流/登录锁定/并发闸使用本地内存实现")
        return
    try:
        import redis.asyncio as aioredis  # 可选依赖

        _client = aioredis.from_url(url, decode_responses=True,
                                    socket_connect_timeout=2, socket_timeout=2)
        _state = "on"
        logger.info("Redis 已启用：%s", _redacted(url))
    except Exception as e:  # 未安装 redis 包 / URL 非法
        _client, _state = None, "error"
        logger.warning("Redis 不可用（%s），自动回退本地内存实现", e)


def _redacted(url: str) -> str:
    # 隐藏可能内嵌的密码，仅用于日志
    if "@" in url:
        scheme, _, rest = url.partition("://")
        _, _, hostport = rest.rpartition("@")
        return f"{scheme}://***@{hostport}"
    return url


def get_redis() -> Optional[Any]:
    """可用则返回异步客户端，否则 None（调用方据此走内存回退）。"""
    _init()
    return _client if _state == "on" else None


def redis_enabled() -> bool:
    _init()
    return _state == "on"


async def ping() -> bool:
    """健康检查：真正探一次活连接，失败则降级并标记不可用。"""
    r = get_redis()
    if r is None:
        return False
    try:
        await r.ping()
        return True
    except Exception as e:
        global _state
        _state = "error"
        logger.warning("Redis ping 失败（%s），本次进程回退本地内存实现", e)
        return False


async def close() -> None:
    global _client, _state
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            pass
    _client, _state = None, "off"
