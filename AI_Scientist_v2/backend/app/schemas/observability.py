from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpanInfo(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    span_type: str
    span_name: str
    project_id: Optional[int]
    task_id: Optional[int]
    input_data: str
    output_data: str
    tokens_used: int
    cost_yuan: float
    status: str
    error_detail: str
    duration_ms: int
    created_at: datetime
    class Config:
        from_attributes = True

class CostSummary(BaseModel):
    total_cost_yuan: float
    total_tokens: int
    call_count: int
    model_breakdown: dict