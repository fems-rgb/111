"""pytest 共享 fixtures

设计：
- 环境变量指向内存/临时 SQLite，避免污染 zhixing.db
- QWEN_API_KEY 设为占位串，让 qwen_client 走"未配置"分支，测试期间不会真调用外部 API
- 提供 httpx.AsyncClient（ASGITransport）绕过 lifespan，只做路由级 smoke
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# ── 在导入 app.* 之前把环境变量塞好 ──
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

_TMP_DB = tempfile.NamedTemporaryFile(prefix="zhixing_test_", suffix=".db", delete=False).name
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TMP_DB}")
os.environ.setdefault("QWEN_API_KEY", "sk-xxxx-test-placeholder")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://testserver"]')


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def temp_db_path() -> str:
    return _TMP_DB


@pytest.fixture
async def client():
    """FastAPI ASGITransport 客户端（不触发 lifespan）"""
    from httpx import ASGITransport, AsyncClient
    from app.main import app  # 延迟导入，让 env 先生效

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver", timeout=10.0) as ac:
        yield ac


def teardown_module(_module=None):
    try:
        if os.path.exists(_TMP_DB):
            os.remove(_TMP_DB)
    except OSError:
        pass
