from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import User, TraceRecord, CostRecord
from app.schemas.observability import SpanInfo, CostSummary
from app.observability.cost_tracker import cost_tracker
from app.api.deps import get_current_user

router = APIRouter(prefix="/observability", tags=["可观测性"])


@router.get("/traces", response_model=list[SpanInfo])
async def get_traces(project_id: int = None, limit: int = 50, offset: int = 0,
                    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(TraceRecord)
    if project_id:
        query = query.where(TraceRecord.project_id == project_id)
    result = await db.execute(query.order_by(TraceRecord.created_at.desc()).offset(offset).limit(limit))
    return [SpanInfo.model_validate(r) for r in result.scalars().all()]


@router.get("/cost", response_model=CostSummary)
async def get_cost(user: User = Depends(get_current_user)):
    return CostSummary.model_validate(cost_tracker.get_summary())


@router.get("/traces/{trace_id}", response_model=list[SpanInfo])
async def get_trace_detail(trace_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TraceRecord).where(TraceRecord.trace_id == trace_id).order_by(TraceRecord.created_at))
    return [SpanInfo.model_validate(r) for r in result.scalars().all()]