"""智研星河 - 数据库初始化 + 种子数据"""
from sqlalchemy import select
from app.database.session import engine, AsyncSessionLocal, Base
from app.database.models import User, UserRole
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def init_database():
    """创建所有表并初始化管理员账号"""
    # 创建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ 数据库表结构已创建")

    # === 自动迁移：为旧库补加新列（SQLite 安全方式）===
    new_columns = [
        ("hypothesis", "TEXT DEFAULT ''"),
        ("verification_method", "TEXT DEFAULT ''"),
        ("visibility", "VARCHAR(20) DEFAULT 'private'"),
        ("closure_stage", "INTEGER DEFAULT -1"),
        ("evidence_files", "JSON DEFAULT '[]'"),
        ("team_config", "JSON DEFAULT '{}'"),
        ("workspace", "VARCHAR(20) DEFAULT 'personal'"),
        ("competition_config", "TEXT"),
    ]
    import sqlite3, os
    db_url = str(engine.url)
    if db_url.startswith("sqlite"):
        db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)

            # 检查 projects 表是否存在
            table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
            if table_check.fetchone():
                cursor = conn.execute("PRAGMA table_info(projects)")
                existing = {row[1] for row in cursor.fetchall()}
                for col_name, col_def in new_columns:
                    if col_name not in existing:
                        conn.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}")
                        logger.info(f"🔧 迁移: projects.{col_name} 已添加")

                # 创建 project_shares 表
                cursor2 = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_shares'")
                if not cursor2.fetchone():
                    conn.execute("""CREATE TABLE project_shares (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL REFERENCES projects(id),
                        target_workspace VARCHAR(20) NOT NULL,
                        shared_by INTEGER NOT NULL REFERENCES users(id),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )""")
                    logger.info("🔧 迁移: project_shares 表已创建")

                # === 迁移: pipelines.is_default ===
                cursor3 = conn.execute("PRAGMA table_info(pipelines)")
                pipe_cols = {row[1] for row in cursor3.fetchall()}
                if "is_default" not in pipe_cols:
                    conn.execute("ALTER TABLE pipelines ADD COLUMN is_default BOOLEAN DEFAULT 0")
                    logger.info("🔧 迁移: pipelines.is_default 已添加")
            else:
                logger.info("ℹ️ projects 表不存在（新库），跳过迁移")

            conn.commit()
            conn.close()
            logger.info("✅ 自动迁移完成")
        else:
            logger.info("ℹ️ 新库，无需迁移")
    # === 迁移结束 ===

    # 创建默认管理员
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == settings.ADMIN_USERNAME)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            from app.security.auth import hash_password
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                display_name="系统管理员",
                role=UserRole.ADMIN,
                institution="智研星河",
                bio="系统默认管理员账号"
            )
            session.add(admin)
            await session.commit()
            logger.info(f"✅ 管理员账号已创建: {settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")
        else:
            logger.info("ℹ️ 管理员账号已存在，跳过初始化")