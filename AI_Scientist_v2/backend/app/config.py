"""智研星枢 v3.0 - 全局配置管理（单例模式）"""
from app.utils.safe_json import safe_json_parse
from app.utils import paths as _paths
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
    QWEN_MODEL_NAME: str = "qwen-plus"          # 全局默认：均衡档（省成本），非专家场景不再默认最贵的 qwen-max
    QWEN_VISION_MODEL: str = "qwen-vl-max"
    QWEN_MAX_TOKENS: int = 8192
    QWEN_TEMPERATURE: float = 0.7
    # 429/5xx 时的单模型重试次数（总计尝试次数，含首次）
    QWEN_MAX_RETRIES: int = 2
    # 首选模型不可用（429 限流 / 403 未开通）时按顺序回退的模型，逗号分隔
    # 成本优先：先试最便宜的 qwen-turbo，再逐级升到 plus / max
    QWEN_FALLBACK_MODELS: str = "qwen-turbo,qwen-plus,qwen-max,qwen-max-longcontext"
    # 通义千问兼容端点（OpenAI Chat Completions 接口），可被 env 覆盖
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    # ── 多模型供应商（均为 OpenAI 兼容 /chat/completions 接口；密钥留空则该供应商不出现）──
    # DeepSeek（深度求索）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_MODELS: str = "deepseek-chat,deepseek-reasoner"
    # Moonshot Kimi
    MOONSHOT_API_KEY: str = ""
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn/v1/chat/completions"
    MOONSHOT_MODELS: str = "moonshot-v1-8k,moonshot-v1-32k,moonshot-v1-128k"
    # 智谱 GLM
    ZHIPU_API_KEY: str = ""
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    ZHIPU_MODELS: str = "glm-4-flash,glm-4-air,glm-4-plus"
    # 自定义通用 OpenAI 兼容端点（Base URL + Key + 逗号分隔模型名，三者齐全才生效）
    CUSTOM_API_KEY: str = ""
    CUSTOM_BASE_URL: str = ""
    CUSTOM_MODELS: str = ""

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

    # ── 路径（一律绝对、固定，见 app/utils/paths.py：换 cwd 启动也不会把文件写到别处）──
    UPLOAD_DIR: str = str(_paths.UPLOADS_ROOT)      # 用户上传的原始文件
    LOG_DIR: str = str(_paths.LOGS_ROOT)
    GENERATED_DIR: str = str(_paths.GENERATED_ROOT)  # 一切生成/派生文件的唯一根目录

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

# 确保必要目录存在（uploads / logs / generated 固定骨架 + .gitkeep）
_paths.ensure_tree()