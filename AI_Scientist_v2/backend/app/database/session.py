"""智研星枢 - 异步数据库引擎"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

_IS_SQLITE = "sqlite" in settings.DATABASE_URL

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # timeout：SQLite 原生 busy 超时（秒）。并发写时排队等待，而不是立刻抛 database is locked
    connect_args={"check_same_thread": False, "timeout": 15} if _IS_SQLITE else {},
    pool_pre_ping=True,
)


if _IS_SQLITE:
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
            await session.close()

if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        # WAL 让读写互不阻塞；busy_timeout 让偶发争用排队等待，而不是直接抛 database is locked
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=15000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()
