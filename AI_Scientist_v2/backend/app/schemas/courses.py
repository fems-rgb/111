"""课程中心数据契约"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    code: str = Field(default="", max_length=50)
    description: str = Field(default="", max_length=2000)
    syllabus: str = Field(default="", max_length=20000)
    domain: str = Field(default="", max_length=100)
    cover_emoji: str = Field(default="📖", max_length=8)
    chapters: Optional[list[dict[str, Any]]] = None
    visibility: str = Field(default="public")
    project_id: Optional[int] = None


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    syllabus: Optional[str] = Field(None, max_length=20000)
    domain: Optional[str] = Field(None, max_length=100)
    cover_emoji: Optional[str] = Field(None, max_length=8)
    chapters: Optional[list[dict[str, Any]]] = None
    visibility: Optional[str] = None
    status: Optional[str] = None


class SlideEditRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    bullets: Optional[list[dict[str, Any]]] = None
    notes: Optional[str] = Field(None, max_length=4000)


class CoursewareUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    slides: Optional[list[dict[str, Any]]] = None


class GenerateDeckRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=300)
    syllabus: str = Field(default="", max_length=20000)
    chapter_count: int = Field(default=6, ge=1, le=20)
    slides_per_chapter: int = Field(default=5, ge=1, le=12)
    style: str = Field(default="标准", max_length=50)
    audience: str = Field(default="本科生", max_length=50)
    domain: str = Field(default="", max_length=100)
    # 联动：多源素材（原资料/科学问题/研究报告/项目/对话/流水线/技能）
    sources: Optional[dict[str, Any]] = None
    reference_doc_id: Optional[int] = None
    project_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=300)
    auto_save: bool = True
    # 课件生成可选模型（为空则用后端默认模型；不在白名单内也会回退默认）
    model: Optional[str] = Field(None, max_length=60)
    # 课件工坊：不传 course_id 时自动建一个仅自己可见的私有课程来承载课件
    course_id: Optional[int] = None
    create_course: bool = True


class AiRefreshRequest(BaseModel):
    slide_indexes: Optional[list[int]] = None   # 不传则全部 risk>=0.4 的页面
    extra_context: str = Field(default="", max_length=8000)
    sources: Optional[dict[str, Any]] = None     # 同上：更新时也能引用外部素材
    reference_doc_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=300)


class SyncPipelineRequest(BaseModel):
    """走研究流水线产出讲义"""
    pipeline_id: str = Field(..., min_length=1, max_length=64)
    run_id: Optional[str] = Field(None, max_length=64)   # 不传则取最近一次成功 run
    topic: Optional[str] = Field(None, max_length=300)
    chapter_count: int = Field(default=5, ge=1, le=15)
    slides_per_chapter: int = Field(default=5, ge=1, le=10)
    skill_runs: Optional[list[dict[str, Any]]] = None    # 额外叠加技能产出
    title: Optional[str] = Field(None, max_length=300)


class ProgressRequest(BaseModel):
    courseware_id: int
    slide_index: int = Field(..., ge=0)
    completed: bool = False


class OutlineRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=20000)
    domain: str = Field(default="", max_length=100)
    sources: Optional[dict[str, Any]] = None
