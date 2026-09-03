from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    research_question: str = Field(..., min_length=1, max_length=10000)
    domain: str = Field(default="人工智能")
    tags: list[str] = Field(default_factory=list)
    hypothesis: str = Field(default="", max_length=10000)
    verification_method: str = Field(default="", max_length=10000)
    visibility: str = Field(default="private")
    evidence_files: list[str] = Field(default_factory=list)
    workspace: str = Field(default="personal")

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    research_question: Optional[str] = None
    domain: Optional[str] = None
    tags: Optional[list[str]] = None
    hypothesis: Optional[str] = None
    verification_method: Optional[str] = None
    visibility: Optional[str] = None
    closure_stage: Optional[int] = None

class ProjectInfo(BaseModel):
    id: int
    title: str
    description: str
    research_question: str
    domain: str
    status: str
    complexity: Optional[str] = None
    final_output: str
    review_score: Optional[float] = None
    tags: list
    hypothesis: str = ""
    verification_method: str = ""
    visibility: str = "private"
    closure_stage: int = -1
    evidence_files: list = []
    workspace: str = "personal"
    shared_workspaces: list[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def _convert_enums(cls, data):
        if hasattr(data, "status") and hasattr(data.status, "value"):
            data = dict(data.__dict__) if not isinstance(data, dict) else data
            if hasattr(data, "status"):
                pass
        if not isinstance(data, dict) and hasattr(data, "__table__"):
            d = {}
            for col in data.__table__.columns:
                val = getattr(data, col.key, None)
                if hasattr(val, "value"):
                    val = val.value
                d[col.key] = val
            d["hypothesis_count"] = 0
            return d
        return data

class ProjectListItem(BaseModel):
    id: int
    title: str
    domain: str
    status: str
    complexity: Optional[str] = None
    tags: list
    hypothesis_count: int = 0
    progress: int = 0
    total_steps: int = 0
    completed_steps: int = 0
    closure_stage: int = -1
    workspace: str = "personal"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def _convert_from_orm(cls, data):
        """将 SQLAlchemy ORM 对象安全转换为 dict，处理枚举和缺失字段"""
        if not isinstance(data, dict) and hasattr(data, "__table__"):
            d = {}
            for col in data.__table__.columns:
                val = getattr(data, col.key, None)
                if hasattr(val, "value"):
                    val = val.value
                d[col.key] = val
            # 补充数据库中不存在的计算字段
            d.setdefault("hypothesis_count", 0)
            return d
        return data
