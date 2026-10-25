from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ChatAttachment(BaseModel):
    file_id: Optional[str] = None
    filename: str
    summary: Optional[str] = None

class ChatSendRequest(BaseModel):
    project_id: Optional[int] = None
    content: str = Field(..., min_length=1, max_length=10000)
    attachments: Optional[list[ChatAttachment]] = None

class ChatMessageInfo(BaseModel):
    id: int
    project_id: Optional[int]
    user_id: int
    role: str
    content: str
    content_type: str
    tokens_used: int
    metadata_: Optional[dict[str, Any]] = Field(None, alias="metadata_")
    is_pinned: bool = False
    created_at: datetime
    class Config:
        from_attributes = True