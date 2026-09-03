import asyncio, sys
sys.path.insert(0, 'D:/AI_Scientist/AI_Scientist/backend')
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text

async def fix():
    engine = create_async_engine(settings.DATABASE_URL)
    async with AsyncSession(engine) as db:
        await db.execute(text("UPDATE projects SET status='failed' WHERE id=1"))
        await db.commit()
        print('OK: project 1 -> failed')

asyncio.run(fix())
