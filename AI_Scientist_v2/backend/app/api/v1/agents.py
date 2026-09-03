from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import User
from app.schemas.agent import AgentInfo, ReviewRequest, DirectChatRequest
from app.agents import get_agent_info, AGENT_REGISTRY
from app.agents.orchestrator import orchestrator
from app.services.agent_service import get_task_detail
from app.agents.qwen_client import call_qwen
from app.security.prompt_guard import prompt_guard
from app.api.deps import get_current_user

router = APIRouter(prefix="/agents", tags=["Agent"])


@router.get("", response_model=list[AgentInfo])
async def list_agents():
    return get_agent_info()


@router.post("/tasks/{task_id}/review")
async def review_task(task_id: int, req: ReviewRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await orchestrator.resume_from_review(db, task_id, user.id, req.comment, req.approved)


@router.post("/chat")
async def direct_chat(req: DirectChatRequest, user: User = Depends(get_current_user)):
    is_safe, reason = prompt_guard.check(req.message)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"安全检测未通过: {reason}")
    agent_cls = AGENT_REGISTRY.get(req.agent_name)
    if agent_cls:
        agent = agent_cls()
        system = agent.system_prompt
    else:
        system = "你是智研星枢AI助手，专注人文社科学术研究。用中文回答，学术严谨但通俗易懂。"
    result = await call_qwen(system, prompt_guard.sanitize_for_llm(req.message), model=req.model)
    return {"reply": result["content"], "tokens": result["tokens"], "model": result["model"], "cost": result["cost"]}