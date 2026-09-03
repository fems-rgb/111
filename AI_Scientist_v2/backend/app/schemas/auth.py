from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    display_name: str = Field(default="", max_length=100)
    role: str = Field(default="student")
    institution: str = Field(default="", max_length=200)

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    role: str
    avatar_url: str
    institution: str
    bio: str
    created_at: datetime
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    user: UserInfo

class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    institution: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str