from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserInfo, UserUpdateRequest, RefreshTokenRequest
from app.services.auth_service import register_user, authenticate_user, generate_tokens
from app.security.auth import decode_refresh_token, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await authenticate_user(db, req.username, req.password)
        tokens = generate_tokens(user)
        return TokenResponse(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"],
                           user=UserInfo.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await register_user(db, req)
        tokens = generate_tokens(user)
        return TokenResponse(access_token=tokens["access_token"], refresh_token=tokens["refresh_token"],
                           user=UserInfo.model_validate(user))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
async def refresh(req: RefreshTokenRequest):
    payload = decode_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="刷新令牌无效")
    return {"access_token": create_access_token({"sub": payload["sub"]}), "token_type": "bearer"}


@router.get("/me", response_model=UserInfo)
async def get_me(user: User = Depends(get_current_user)):
    return UserInfo.model_validate(user)


@router.patch("/me")
async def update_me(req: UserUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    for field in ["display_name", "institution", "avatar_url", "bio"]:
        val = getattr(req, field, None)
        if val is not None:
            setattr(user, field, val)
    await db.commit()
    return {"message": "更新成功"}