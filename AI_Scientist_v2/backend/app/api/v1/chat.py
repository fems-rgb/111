from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.session import get_db
from app.database.models import User, ChatMessage
from app.schemas.chat import ChatSendRequest, ChatMessageInfo
from app.services.chat_service import chat_with_ai, get_chat_history
from app.api.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("/send")
async def send(req: ChatSendRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        attachments = [a.model_dump() for a in req.attachments] if req.attachments else None
        return await chat_with_ai(db, user.id, req.content, req.project_id, attachments=attachments)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=list[ChatMessageInfo])
async def history(project_id: int = None, limit: int = 50,
                  user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return [ChatMessageInfo.model_validate(m) for m in await get_chat_history(db, user.id, project_id, limit)]


@router.delete("/history")
async def delete_history(project_id: int = None,
                         user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除当前用户的对话历史"""
    query = delete(ChatMessage).where(ChatMessage.user_id == user.id)
    if project_id:
        query = query.where(ChatMessage.project_id == project_id)
    result = await db.execute(query)
    await db.commit()
    return {"deleted": result.rowcount, "message": f"已删除 {result.rowcount} 条消息"}


@router.delete("/messages/{message_id}")
async def delete_message(message_id: int,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """删除单条消息（仅本人）"""
    msg = (await db.execute(
        select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.user_id == user.id)
    )).scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在或无权访问")
    await db.delete(msg)
    await db.commit()
    return {"ok": True, "deleted_id": message_id}


@router.post("/messages/{message_id}/pin")
async def toggle_pin(message_id: int,
                      user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """切换消息置顶状态"""
    msg = (await db.execute(
        select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.user_id == user.id)
    )).scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在或无权访问")
    msg.is_pinned = not msg.is_pinned
    await db.commit()
    return {"ok": True, "id": message_id, "is_pinned": msg.is_pinned}
