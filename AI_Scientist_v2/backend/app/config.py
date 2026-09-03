"""智研星枢 v3.0 - 全局配置管理（单例模式）"""
from app.utils.safe_json import safe_json_parse
from pydantic_settings import BaseSettings
from typing import List
import json, os

class Settings(BaseSettings):
    # ── 应用 ──
    APP_NAME: str = "智研星枢"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── 数据库 ──
    DATABASE_URL: str = "sqlite+aiosqlite:///./zhixing.db"

    # ── 通义千问 ──
    QWEN_API_KEY: str = ""
    QWEN_MODEL_NAME: str = "qwen-max"
    QWEN_VISION_MODEL: str = "qwen-vl-max"
    QWEN_MAX_TOKENS: int = 8192
    QWEN_TEMPERATURE: float = 0.7

    # ── 安全 ──
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_ORIGINS: str = '["http://localhost:5173"]'

    # ── 可观测性 ──
    TRACE_RETENTION_DAYS: int = 30
    COST_ALERT_THRESHOLD_YUAN: float = 100.0
    LOG_LEVEL: str = "DEBUG"

    # ── 管理员 ──
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123456"
    ADMIN_EMAIL: str = "admin@zhixing.ai"

    # ── 路径 ──
    UPLOAD_DIR: str = "uploads"
    LOG_DIR: str = "logs"

    @property
    def allowed_origins_list(self) -> List[str]:
        try:
            result=safe_json_parse(self.ALLOWED_ORIGINS,fallback=None,label="config/ALLOWED_ORIGINS")
            if result is None:
                result=[o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
            return result
        except Exception:
            return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保必要目录存在
for d in [settings.UPLOAD_DIR, settings.LOG_DIR]:
    os.makedirs(d, exist_ok=True)