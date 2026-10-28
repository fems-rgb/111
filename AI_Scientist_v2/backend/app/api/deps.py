from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import User, UserRole
from app.security.auth import decode_access_token
from app.security.rate_limiter import rate_limiter, auth_rate_limiter

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
                           db: AsyncSession = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌格式错误")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def _client_ip(request: Request) -> str:
    """取真实客户端 IP：反代后 request.client.host 会是代理地址，优先 X-Forwarded-For 首个。
    （仅在信任的 Nginx/Caddy 反代后有效；直连部署仍用 socket 地址。）"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request):
    key = _client_ip(request)
    allowed, retry_after = await rate_limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"请求过于频繁，请{retry_after}秒后重试",
                          headers={"Retry-After": str(retry_after)})


async def check_auth_rate_limit(request: Request):
    """登录/注册频率护城河：每 IP 限次，抵御撞库、暴力尝试与高频请求卡死"""
    key = _client_ip(request)
    allowed, retry_after = await auth_rate_limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"登录/注册尝试过于频繁，请{retry_after}秒后再试",
                          headers={"Retry-After": str(retry_after)})

async def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    token: str = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """支持Header Bearer Token 或 Query Param token 两种认证方式（SSE需要）"""
    actual_token = None
    if credentials:
        actual_token = credentials.credentials
    elif token:
        actual_token = token
    if not actual_token:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    payload = decode_access_token(actual_token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌格式错误")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user