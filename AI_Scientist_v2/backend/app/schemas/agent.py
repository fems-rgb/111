from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone

class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    requires_review: bool

class TaskInfo(BaseModel):
    id: int
    project_id: int
    agent_name: str
    step_order: int
    status: str
    output_data: str
    error_message: str
    retry_count: int
    requires_review: bool
    review_comment: str
    tokens_used: int
    cost_yuan: float
    model_used: str

    @field_validator('started_at', 'finished_at', mode='before')
    @classmethod
    def ensure_utc(cls, v):
        if v is not None and isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    class Config:
        from_attributes = True

class ReviewRequest(BaseModel):
    approved: bool
    comment: str = Field(default="", max_length=2000)

class DirectChatRequest(BaseModel):
    agent_name: str = Field(default="general")
    message: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="qwen-max")

# === 新增：运行模式定义 ===
from typing import Literal
RunMode = Literal["quick", "expert"]
