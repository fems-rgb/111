"""智研星枢 - 完整数据库模型（12张表+实验场）"""
import uuid
from datetime import datetime
from sqlalchemy import (Boolean,
    Column, Integer, String, Text, DateTime, Float,
    ForeignKey, JSON, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
import enum


# ════════════════════════════════════════════════════════════
#  枚举定义
# ════════════════════════════════════════════════════════════

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Complexity(str, enum.Enum):
    SIMPLE = "simple"
    WORKFLOW = "workflow"
    MULTI_AGENT = "multi_agent"


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    REVIEW = "review"


# ════════════════════════════════════════════════════════════
#  用户表
# ════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100), default="")
    role = Column(SAEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    avatar_url = Column(String(500), default="")
    institution = Column(String(200), default="")
    bio = Column(Text, default="")
    preferences = Column(JSON, default=dict)  # 用户偏好设置
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


# ════════════════════════════════════════════════════════════
#  项目表
# ════════════════════════════════════════════════════════════

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    research_question = Column(Text, nullable=False)
    domain = Column(String(100), default="人文社科")
    status = Column(SAEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    complexity = Column(SAEnum(Complexity), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    config = Column(JSON, default=dict)       # 模型选择、参数等
    metadata_ = Column("metadata", JSON, default=dict)
    final_output = Column(Text, default="")   # 最终成果汇总
    competition_config = Column(Text, nullable=True, comment="赛题参赛配置JSON")
    review_score = Column(Float, nullable=True)  # 评审分数
    tags = Column(JSON, default=list)          # 标签列表
    hypothesis = Column(Text, default="")      # 候选假设
    verification_method = Column(Text, default="")  # 验证方法
    visibility = Column(String(20), default="private")  # private/lab/public
    workspace = Column(String(20), default="personal")  # personal/lab/classroom/enterprise
    closure_stage = Column(Integer, default=-1)  # -1=未开始 0=假设 1=设计 2=执行 3=反馈
    evidence_files = Column(JSON, default=list)
    team_config = Column(JSON, default=dict)  # 证据文件file_id列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    owner = relationship("User", back_populates="projects")
    tasks = relationship("AgentTask", back_populates="project", cascade="all, delete-orphan",
                         order_by="AgentTask.step_order")
    traces = relationship("TraceRecord", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")


# ════════════════════════════════════════════════════════════
#  Agent任务表
# ════════════════════════════════════════════════════════════

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String(32), default=TaskStatus.PENDING.value, nullable=False)

    # 输入输出
    input_data = Column(Text, default="")
    output_data = Column(Text, default="")
    error_message = Column(Text, default="")

    # 断点恢复
    checkpoint = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 人工审核
    requires_review = Column(Boolean, default=False)
    review_comment = Column(Text, default="")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # 成本追踪
    tokens_used = Column(Integer, default=0)
    cost_yuan = Column(Float, default=0.0)
    model_used = Column(String(50), default="")

    # 时间
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="tasks")


# ════════════════════════════════════════════════════════════
#  追踪记录表
# ════════════════════════════════════════════════════════════

class TraceRecord(Base):
    __tablename__ = "trace_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    trace_id = Column(String(64), index=True, nullable=False)
    parent_span_id = Column(String(64), nullable=True)
    span_id = Column(String(64), index=True, nullable=False)

    # 追踪内容
    span_type = Column(String(30))   # llm_call / tool_call / agent_step / human_review
    span_name = Column(String(200))
    input_data = Column(Text, default="")
    output_data = Column(Text, default="")

    # 元数据
    metadata_ = Column("metadata", JSON, default=dict)
    tokens_used = Column(Integer, default=0)
    cost_yuan = Column(Float, default=0.0)
    duration_ms = Column(Integer, default=0)
    status = Column(String(20), default="ok")
    error_detail = Column(Text, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="traces")


# ════════════════════════════════════════════════════════════
#  成本汇总表
# ════════════════════════════════════════════════════════════

class CostRecord(Base):
    __tablename__ = "cost_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    date = Column(String(10), index=True)
    model_name = Column(String(50))
    total_tokens = Column(Integer, default=0)
    total_cost_yuan = Column(Float, default=0.0)
    call_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CostDaily(Base):
    """全站 API 成本的按天快照（成本预测/预警的数据源）

    热路径只累内存日桶，由 prediction.flush_cost_daily 低频镜像进来；
    重启后日桶从本表恢复历史（当天已落库部分会被内存桶覆盖，不丢数据）。
    """
    __tablename__ = "cost_daily"

    day = Column(String(10), primary_key=True)   # YYYY-MM-DD
    cost_yuan = Column(Float, default=0.0)
    calls = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ════════════════════════════════════════════════════════════
#  审计日志表
# ════════════════════════════════════════════════════════════

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), index=True)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    detail = Column(JSON, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ════════════════════════════════════════════════════════════
#  聊天消息表
# ════════════════════════════════════════════════════════════

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20))    # user / assistant / system
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text / markdown / code / image
    metadata_ = Column("metadata", JSON, default=dict)
    tokens_used = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)  # 置顶消息
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="messages")


# ════════════════════════════════════════════════════════════
#  通知表
# ════════════════════════════════════════════════════════════

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    type = Column(SAEnum(NotificationType), default=NotificationType.INFO)
    is_read = Column(Boolean, default=False)
    action_url = Column(String(500), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


# ════════════════════════════════════════════════════════════
#  工具调用记录表
# ════════════════════════════════════════════════════════════

class ToolCallRecord(Base):
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String(64), index=True)
    task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    tool_name = Column(String(50), nullable=False)
    tool_input = Column(Text, default="")
    tool_output = Column(Text, default="")
    status = Column(String(20), default="ok")
    duration_ms = Column(Integer, default=0)
    error_detail = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ════════════════════════════════════════════════════════════
#  知识库文档表
# ════════════════════════════════════════════════════════════

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(300), nullable=False)
    saved_name = Column(String(200), nullable=False)
    file_ext = Column(String(10), nullable=False)
    file_size = Column(Integer, default=0)
    description = Column(Text, default="")
    summary = Column(Text, default="")
    structured_data = Column(JSON, default=dict)
    parse_status = Column(String(20), default="pending")
    tokens_used = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ════════════════════════════════════════════════════════════
#  分片上传记录表（断点续传）
# ════════════════════════════════════════════════════════════

class UploadChunk(Base):
    __tablename__ = "upload_chunks"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(300), nullable=False)
    total_size = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_hash = Column(String(64), nullable=False)
    saved_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class CustomSkill(Base):
    __tablename__ = "custom_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(10), default="🔧")
    prompt_template = Column(Text, default="")
    category = Column(String(50), default="custom")
    is_public = Column(Boolean, default=True)
    webhook_url = Column(String(500), default="")
    webhook_method = Column(String(10), default="POST")
    # 联动字段：关联的资料库文件ID列表、关联的项目ID
    linked_doc_ids = Column(JSON, default=list)
    linked_project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ProjectShare(Base):
    __tablename__ = "project_shares"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    target_workspace = Column(String(20), nullable=False)
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project")
    sharer = relationship("User")

# ════════════════════════════════════════════════════════════
#  赛道一科研闭环扩展表（2026-08 增量新增，不动现有 12 张表）
# ════════════════════════════════════════════════════════════

class Hypothesis(Base):
    """科学假设 + 证据链 + 迭代版本链"""
    __tablename__ = "hypotheses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    hypo_id = Column(String(16), default="H1")
    statement = Column(Text, default="")
    variables = Column(JSON, default=list)
    testability_score = Column(Float, default=0.0)
    suggested_method = Column(Text, default="")
    evidence_chain = Column(Text, default="")
    version = Column(Integer, default=1)
    parent_id = Column(Integer, nullable=True)
    status = Column(String(32), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IterationRecord(Base):
    """假设→实验→反馈 闭环轨迹（自迭代曲线数据源）"""
    __tablename__ = "iteration_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    iteration_num = Column(Integer, default=1)
    hypothesis_snapshot = Column(JSON, default=list)
    experiment_result = Column(Text, default="")
    feedback = Column(Text, default="")
    score_before = Column(Float, default=0.0)
    score_after = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Pipeline(Base):
    """持久化流水线（替换 automation.py 内存字典）"""
    __tablename__ = "pipelines"

    id = Column(String(32), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    steps = Column(JSON, default=list)
    trigger = Column(String(32), default="manual")
    schedule_cron = Column(String(64), default="")
    status = Column(String(32), default="idle")
    is_default = Column(Boolean, default=False, index=True)
    run_count = Column(Integer, default=0)
    last_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PipelineRun(Base):
    """流水线运行记录"""
    __tablename__ = "pipeline_runs"

    id = Column(String(32), primary_key=True)
    pipeline_id = Column(String(32), ForeignKey("pipelines.id"), nullable=False, index=True)
    status = Column(String(32), default="running")
    steps_log = Column(JSON, default=list)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class PipelineRunLog(Base):
    __tablename__ = "pipeline_run_logs"
    id        = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    run_id    = Column(String(36), ForeignKey("pipeline_runs.id"), index=True)
    level     = Column(String(16), default="INFO")
    message   = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)



# ════════════════════════════════════════════════════════════
#  科学问题题库表（赛道一 · Science 125）
# ════════════════════════════════════════════════════════════

class ScienceQuestion(Base):
    """Science 125 科学问题题库"""
    __tablename__ = "science_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    title_en = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False)
    description = Column(Text, default="")
    keywords = Column(JSON, default=list)
    difficulty = Column(String(20), default="medium")
    source = Column(String(50), default="science_125")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class QuestionTask(Base):
    """题目生成任务记录"""
    __tablename__ = "question_tasks"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("science_questions.question_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")
    result = Column(JSON, default=dict)
    document_path = Column(String(500), nullable=True)
    version = Column(Integer, default=1)
    feedback = Column(Text, default="")
    error_message = Column(Text, default="")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    progress = Column(Integer, default=0)  # 0-100 生成进度

# ============================================================
#  实验场运行记录表
# ============================================================

class ExperimentRun(Base):
    """实验场模拟运行记录"""
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    question_task_id = Column(Integer, nullable=True, index=True)
    title = Column(String(200), default="")
    code = Column(Text, default="")
    status = Column(String(20), default="pending")
    output_text = Column(Text, default="")
    charts = Column(JSON, default=list)
    video_path = Column(String(500), nullable=True)
    data_table = Column(JSON, nullable=True)
    error_message = Column(Text, default="")
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ExperimentTemplate(Base):
    """实验模板 - 动态管理"""
    __tablename__ = "experiment_templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default='')
    code = Column(Text, nullable=False)
    category = Column(String(100), default='通用')
    is_builtin = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ════════════════════════════════════════════════
#  课程中心（在线教育模块：老师开课 / 学生上课）
# ════════════════════════════════════════════════

class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Course(Base):
    """课程：老师创建、可上传课件、发布后学生可选修"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    code = Column(String(50), default="")
    description = Column(Text, default="")
    syllabus = Column(Text, default="")            # 教学大纲（AI 生成课件的依据）
    chapters = Column(JSON, default=list)          # [{title, points:[]}]
    domain = Column(String(100), default="")
    status = Column(SAEnum(CourseStatus), default=CourseStatus.DRAFT)
    visibility = Column(String(20), default="public")   # public / private
    cover_emoji = Column(String(8), default="📖")
    enroll_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # 联动：讲义可源自研究项目
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    teacher = relationship("User", foreign_keys=[teacher_id])
    coursewares = relationship("Courseware", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Courseware(Base):
    """课件：一份 PPT/PDF 或 AI 生成的幻灯片集，带版本链"""
    __tablename__ = "coursewares"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    source_type = Column(String(20), default="upload")     # upload / ai_generated
    source_path = Column(String(500), default="")          # 原始文件相对路径
    file_size = Column(Integer, default=0)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # 联动：资料库/RAG
    slide_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")          # pending/converting/ready/failed
    error_message = Column(Text, default="")
    version = Column(Integer, default=1)
    parent_id = Column(Integer, ForeignKey("coursewares.id"), nullable=True)  # AI 刷新后的版本链
    staleness_report = Column(JSON, default=dict)           # 体检结果摘要
    read_size_kb = Column(Integer, default=0)               # 转换后体积（体现优化效果）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="coursewares")
    slides = relationship("Slide", back_populates="courseware", cascade="all, delete-orphan",
                          order_by="Slide.slide_index")


class Slide(Base):
    """单页幻灯片：文本层 + 瘦身后的图片，支撑电子书式阅读"""
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    courseware_id = Column(Integer, ForeignKey("coursewares.id"), nullable=False, index=True)
    slide_index = Column(Integer, default=0)                # 0-based
    title = Column(String(500), default="")
    bullets = Column(JSON, default=list)                    # [{level, text}] 可选中/可搜索文本层
    notes = Column(Text, default="")                        # 演讲者备注
    tables = Column(JSON, default=list)                     # [[cell, ...], ...]
    image_path = Column(String(500), default="")            # 压缩后图相对路径
    image_kb = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)                 # AI 陈旧度风险 0~1
    risk_category = Column(String(50), default="")
    ai_reason = Column(Text, default="")
    ai_suggestion = Column(Text, default="")                # 建议更新后的正文
    updated_by_ai = Column(Boolean, default=False)

    courseware = relationship("Courseware", back_populates="slides")


class Enrollment(Base):
    """选课与学习进度"""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    progress = Column(Integer, default=0)                   # 0-100
    last_courseware_id = Column(Integer, nullable=True)
    last_slide_index = Column(Integer, default=0)
    read_slides = Column(JSON, default=list)                # ["cw:{id}:{idx}", ...]
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="enrollments")
    student = relationship("User", foreign_keys=[student_id])


class GenerateJob(Base):
    """课件生成作业进度（持久化）

    内存表只在进程内且有 TTL，服务重启/超期即查不到；本表低频镜像作业状态，
    让前端在服务重启或作业完成很久后仍能轮询到最终结果。启动时把残留 running 判为失败。
    """
    __tablename__ = "generate_jobs"

    job_id = Column(String(32), primary_key=True)
    user_id = Column(Integer, nullable=True, index=True)
    topic = Column(String(500), default="")
    course_id = Column(Integer, nullable=True)
    course_title = Column(String(500), default="")
    status = Column(String(20), default="running")           # running / done / failed
    stage = Column(String(30), default="queued")             # queued/material/outline/chapter/summary/render/persist/done/failed
    percent = Column(Integer, default=0)                     # 0-100
    message = Column(String(500), default="")
    chapters_done = Column(Integer, default=0)
    chapters_total = Column(Integer, default=0)
    slides_done = Column(Integer, default=0)
    slides_total = Column(Integer, default=0)
    result = Column(JSON, default=dict)                      # 完成时放 _build_deck 返回值
    error = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ════════════════════════════════════════════════════════════
#  AI 通识课（面向非专业学习者的图文微课）
#  独立建表，不动现有 Course/Courseware，避免影响课程中心与课件工坊
# ════════════════════════════════════════════════════════════

class GeneralCourse(Base):
    """一门通识课：课程广场的卡片 + 章节容器"""
    __tablename__ = "general_courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(300), default="")
    emoji = Column(String(16), default="🌱")
    category = Column(String(50), default="AI 入门", index=True)
    level = Column(String(20), default="零基础")          # 零基础 / 进阶 / 专题
    summary = Column(Text, default="")
    tags = Column(JSON, default=list)
    cover_image = Column(String(300), default="")            # 封面插画（generated/general/ 下的相对路径）
    status = Column(String(20), default="draft", index=True)   # draft / published
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    lesson_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lessons = relationship("GeneralLesson", back_populates="course",
                           cascade="all, delete-orphan",
                           order_by="GeneralLesson.order_index")


class GeneralLesson(Base):
    """一节课：Markdown 正文（电子书渲染）+ 随堂自测"""
    __tablename__ = "general_lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("general_courses.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    order_index = Column(Integer, default=0, index=True)
    title = Column(String(200), nullable=False)
    kicker = Column(String(100), default="")
    summary = Column(Text, default="")
    content = Column(Text, default="")                    # Markdown 正文
    quiz = Column(JSON, default=list)                     # [{q,options,answer,explain}]
    figure = Column(JSON, default=list)                   # 图解块：[{kind,...}]，前端矢量渲染
    cover_image = Column(String(300), default="")         # 本节插画（generated/general/ 下的相对路径）
    minutes = Column(Integer, default=6)
    status = Column(String(20), default="pending")        # pending / ready
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("GeneralCourse", back_populates="lessons")


class KnowledgeGraph(Base):
    """通用知识图谱缓存（Phase C）

    一张表承载四个 scope：general(通识课) / kb(知识库) / project(研究项目) /
    syllabus(课程大纲)。nodes/edges 存原始 JSON，前端自研 SVG 力导向消费。
    project 由外键直接组装零 LLM；其余三个 scope 由 call_qwen 一次抽取。
    """
    __tablename__ = "knowledge_graphs"
    __table_args__ = (UniqueConstraint("scope", "scope_id", name="uq_kg_scope"),)

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(16), nullable=False, index=True)      # general / kb / project / syllabus
    scope_id = Column(String(64), nullable=False, index=True)   # 课程/项目/用户 id（kb 按 user）
    nodes = Column(JSON, default=list)                          # [{id,label,group}]
    edges = Column(JSON, default=list)                          # [[source,target,relation]]
    status = Column(String(16), default="ready")                # ready / empty
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    model_used = Column(String(64), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GeneralProgress(Base):
    """学习进度：按 (user, lesson) 唯一，用于课程卡片完成度与续学定位"""
    __tablename__ = "general_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_gp_user_lesson"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("general_courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("general_lessons.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="learning")       # learning / done
    percent = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
