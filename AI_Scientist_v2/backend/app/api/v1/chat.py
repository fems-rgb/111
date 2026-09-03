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
        return await chat_with_ai(db, user.id, req.content, req.project_id)
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
