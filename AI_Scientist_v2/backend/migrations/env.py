"""Alembic 迁移环境（异步版）

设计要点：
- URL 优先从 `-x db_url=...` 取，否则从 `app.config.settings.DATABASE_URL` 取
- 目标元数据 = `app.database.session.Base.metadata`
  （models.py 里所有表都注册到该 Base）
- SQLite 走 sync driver 生成迁移；运行时仍用 aiosqlite
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 让 `from app.xxx import ...` 在 alembic CLI 下也能生效
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(HERE)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.config import settings  # noqa: E402
from app.database import models  # noqa: E402,F401  确保所有表注册到 Base
from app.database.session import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # CI 中 loggers 段缺失时不阻塞
        pass

# 允许 `alembic -x db_url=... upgrade head` 覆盖
_x_url = context.get_x_argument(as_dictionary=True).get("db_url")
target_url = _x_url or settings.DATABASE_URL

# SQLite 用 sync URL；async driver 名去掉 +aiosqlite/+asyncpg
if "+aiosqlite" in target_url:
    sync_url = target_url.replace("+aiosqlite", "")
elif "+asyncpg" in target_url:
    sync_url = target_url.replace("+asyncpg", "+psycopg2")
else:
    sync_url = target_url

config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=sync_url.startswith("sqlite"),  # SQLite ALTER 兼容
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=sync_url.startswith("sqlite"),
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
