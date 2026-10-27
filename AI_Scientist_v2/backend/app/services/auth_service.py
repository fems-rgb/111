from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool
from app.database.models import User, UserRole
from app.security.auth import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest
import logging

logger = logging.getLogger(__name__)
ROLE_MAP = {"student": UserRole.STUDENT, "teacher": UserRole.TEACHER, "researcher": UserRole.RESEARCHER}


async def register_user(db: AsyncSession, req: RegisterRequest) -> User:
    if (await db.execute(select(User).where(User.username == req.username))).scalar_one_or_none():
        raise ValueError("用户名已被注册")
    if (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none():
        raise ValueError("邮箱已被注册")
    user = User(username=req.username, email=req.email,
                # bcrypt 故意耗时，放线程池执行，避免阻塞 async 事件循环（否则并发注册会卡死全站）
                hashed_password=await run_in_threadpool(hash_password, req.password),
                display_name=req.display_name or req.username, role=ROLE_MAP.get(req.role, UserRole.STUDENT),
                institution=req.institution)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("用户名或密码错误")
    # bcrypt 校验耗时，放线程池，避免洪峰登录阻塞事件循环
    ok = await run_in_threadpool(verify_password, password, user.hashed_password)
    if not ok:
        raise ValueError("用户名或密码错误")
    if not user.is_active:
        raise ValueError("账号已被禁用")
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    return user


def generate_tokens(user: User) -> dict:
    return {"access_token": create_access_token({"sub": str(user.id), "username": user.username, "role": user.role.value}),
            "refresh_token": create_refresh_token({"sub": str(user.id)})}