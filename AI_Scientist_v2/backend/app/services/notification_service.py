from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.database.models import Notification, NotificationType
import logging

logger = logging.getLogger(__name__)


async def create_notification(db: AsyncSession, user_id: int, title: str, content: str = "", ntype: str = "info") -> Notification:
    tm = {"info": NotificationType.INFO, "success": NotificationType.SUCCESS, "warning": NotificationType.WARNING,
          "error": NotificationType.ERROR, "review": NotificationType.REVIEW}
    n = Notification(user_id=user_id, title=title, content=content, type=tm.get(ntype, NotificationType.INFO))
    db.add(n)
    await db.commit()
    return n


async def get_notifications(db: AsyncSession, user_id: int, unread_only: bool = False, limit: int = 20) -> list:
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    result = await db.execute(query.order_by(Notification.created_at.desc()).limit(limit))
    return result.scalars().all()


async def mark_all_read(db: AsyncSession, user_id: int):
    await db.execute(update(Notification).where(Notification.user_id == user_id, Notification.is_read == False).values(is_read=True))
    await db.commit()


async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(func.count(Notification.id)).where(Notification.user_id == user_id, Notification.is_read == False))
    return result.scalar() or 0