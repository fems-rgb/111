"""智研星枢 - 异步数据库引擎

同一套代码兼容 SQLite（默认、零依赖，适合开发/单机）与 PostgreSQL/MySQL（生产横向扩展）：
把 DATABASE_URL 换成 postgresql+asyncpg://... 或 mysql+asyncmy://... 即自动启用连接池，
SQLite 分支则维持 WAL + busy_timeout 的并发姿势。
"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

DATABASE_URL = settings.DATABASE_URL
_IS_SQLITE = "sqlite" in DATABASE_URL

if _IS_SQLITE:
    # 单文件、写者有限：固定小池即可，靠 WAL 让读写互不阻塞
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False, "timeout": 15},
        pool_pre_ping=True,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        """SQLite 并发姿势：WAL + 忙等

        默认的 rollback journal 模式下，读事务会挡住写事务提交，后台生成作业
        （几分钟的 LLM 调用期间一直持着读事务）会把其他写请求全卡成 database is locked。
        WAL 让读写互不阻塞，busy_timeout 让偶发争用排队等待而不是直接 500。
        """
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=15000")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
else:
    # PostgreSQL / MySQL：真正的连接池，支撑多并发与横向扩展
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    )


AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


async def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
