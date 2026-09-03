"""API路由注册"""
from app.api.projects import router as projects_router
from app.api.documents import router as documents_router

all_routers = [projects_router, documents_router]
