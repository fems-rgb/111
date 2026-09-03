from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GenerateRequest(BaseModel):
    question_id: int
    custom_prompt: str = ""


class FeedbackRequest(BaseModel):
    task_id: int
    feedback: str = Field(..., min_length=1, max_length=5000)


class QuestionItem(BaseModel):
    question_id: int
    title: str
    title_en: Optional[str] = None
    category: str
    description: Optional[str] = ""
    keywords: list[str] = []
    difficulty: str = "medium"


class QuestionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[QuestionItem]


class CategoryStat(BaseModel):
    category: str
    count: int


class TaskStatusResponse(BaseModel):
    task_id: int
    question_id: int
    status: str
    result: Optional[dict] = None
    document_path: Optional[str] = None
    version: int = 1
    feedback: Optional[str] = ""
    error_message: Optional[str] = ""
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class MyTaskItem(BaseModel):
    task_id: int
    question_id: int
    status: str
    version: int = 1
    created_at: Optional[str] = None


class MyTasksResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MyTaskItem]
