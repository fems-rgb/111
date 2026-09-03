"""文档生成API路由"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.api.deps import get_current_user, check_rate_limit
from app.database.models import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


class GenerateDocumentRequest(BaseModel):
    research_question: str = Field(..., min_length=10, max_length=2000)
    context: str = Field(default="", max_length=20000)
    template_id: str = Field(default="nh_202619_track1")
    max_quality_iterations: int = Field(default=3, ge=1, le=5)
    token_budget: int = Field(default=80000, ge=10000, le=200000)


@router.post("/generate")
async def generate_document(
    req: GenerateDocumentRequest,
    user: User = Depends(get_current_user),
    _rate: None = Depends(check_rate_limit),
):
    """生成多Agent协作文档（含质量门禁循环）"""
    from app.services.doc_engine import DocumentEngine
    engine = DocumentEngine()
    result = await engine.generate_document(
        research_question=req.research_question,
        context=req.context,
        template_id=req.template_id,
        max_quality_iterations=req.max_quality_iterations,
        token_budget=req.token_budget,
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "生成失败"))
    return {"success": True, "data": result}
