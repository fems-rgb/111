"""智研星枢 v3.0 - FastAPI主入口"""
import sys as _sys
if _sys.platform == "win32":
    # Windows cmd 默认 GBK，中文字体/emoji print 会 UnicodeEncodeError
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
        _sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from contextlib import asynccontextmanager
from pathlib import Path
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database.init_db import init_database
from app.database import models  # noqa: F401
from app.database.session import engine, Base
from app.scheduler import register_pipeline_jobs
from app.observability.logger import setup_logging
from app.core.exceptions import global_exception_handler, AppException
from app.api.v1 import auth, projects, agents, chat, observability, admin, stream, multimodal, knowledge, skills, automation, knowledge_external, export, batch_run, team, questions, evidence, documents, courses, general_courses, alerts, graphs
from app.api.v1.experiment_lab import router as experiment_lab_router

# 前端构建产物路径（优先 frontend/dist 开发模式，后补 backend/static 预构建分发）
_candidates = [
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent.parent / "static",
]
FRONTEND_DIST = next((p for p in _candidates if (p / "index.html").exists()), _candidates[0])

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.DEBUG)
    # 生成文件固定根目录：所有 AI/流水线/课件/实验/PDF 产物都落这里，与启动 cwd 无关
    from app.utils import paths as _paths
    _paths.ensure_tree()
    logger.info(f"📁 生成文件目录（固定）: {_paths.GENERATED_ROOT}")
    await init_database()
    # 确保所有 ORM 模型对应的表都存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 注册定时任务 + 清理僵尸（从旧 on_event 迁移）
    register_pipeline_jobs()
    # 启动自动进度同步（每 5s 把 agent_tasks 完成比例写回 question_tasks.progress）
    from app.core.progress_sync import start_progress_sync
    start_progress_sync()
    from app.database.session import AsyncSessionLocal
    from app.agents.orchestrator import orchestrator
    async with AsyncSessionLocal() as db:
        await orchestrator.cleanup_zombies(db)
    # 课件生成作业对账：上次进程遗留的 running 后台任务已随进程消失，判为失败并清理过期记录
    from app.services import generate_progress as _gp
    _n_job = await _gp.reconcile_on_startup()
    if _n_job:
        logger.info(f"🧹 课件生成作业：重启时标记 {_n_job} 个中断作业为失败")
    # 初始化实验模板
    from app.api.v1.experiment_lab import seed_builtin_templates
    from app.database.session import AsyncSessionLocal as _ASL
    async with _ASL() as _db:
        await seed_builtin_templates(_db)
    # 通识课种子：表为空时铺一门已发布示例课，保证登录即有内容可学
    from app.api.v1.general_seed import seed_general_courses as _seed_gc
    async with _ASL() as _db:
        await _seed_gc(_db)
    yield

app = FastAPI(
    redirect_slashes=True,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    description="基于国产开源大模型的多智能体人文社科科研平台",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)

# ── API 路由 ──
app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(observability.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(stream.router, prefix="/api/v1")
app.include_router(multimodal.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(knowledge_external.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(team.router, prefix="/api/v1")
app.include_router(batch_run.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(experiment_lab_router, prefix="/api/v1")
# ── 课程中心（开课/选课/课件电子化/AI 更新） ──
app.include_router(courses.router, prefix="/api/v1")
app.include_router(courses.cw_router, prefix="/api/v1")
# ── AI 通识课（人人都要学的图文微课） ──
app.include_router(general_courses.router, prefix="/api/v1")
# ── 预警中心（成本/模型/供应商密钥/任务失败聚合） ──
app.include_router(alerts.router, prefix="/api/v1")
# ── 通用知识图谱（general/kb/project/syllabus 四 scope） ──
app.include_router(graphs.router, prefix="/api/v1")
# [FIXED] duplicate multimodal router removed

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "name": settings.APP_NAME}

# ── 前端静态文件服务（仅在构建产物存在时启用）──
if FRONTEND_DIST.exists():
    # 挂载 assets 等静态资源目录
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA Fallback: 优先返回匹配的静态文件，否则返回 index.html"""
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    print(f"✅ 前端构建产物已加载: {FRONTEND_DIST}")
else:
    print(f"⚠️ 未找到前端构建产物: {FRONTEND_DIST}，仅 API 模式运行")
