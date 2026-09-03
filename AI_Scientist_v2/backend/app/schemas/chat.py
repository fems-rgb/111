from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatSendRequest(BaseModel):
    project_id: Optional[int] = None
    content: str = Field(..., min_length=1, max_length=10000)

class ChatMessageInfo(BaseModel):
    id: int
    project_id: Optional[int]
    user_id: int
    role: str
    content: str
    content_type: str
    tokens_used: int
    created_at: datetime
    class Config:
        from_attributes = True