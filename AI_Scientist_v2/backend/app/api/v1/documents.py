"""Document Engine API - document generation and review endpoints"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.doc_engine import DocumentEngine
from app.agents.doc_reviewer import SectionReviewerAgent, DocumentReviewerAgent
from app.contracts.document_template import get_template, list_templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


# ── Request/Response Models ──

class GenerateRequest(BaseModel):
    research_question: str = Field(..., description="研究问题")
    context: str = Field(default="", description="研究背景/上下文")
    template_id: str = Field(default="nh_202619_track1", description="文档模板ID")

class ReviewSectionRequest(BaseModel):
    research_question: str
    context: str = ""
    section_id: str
    section_content: str
    template_id: str = "nh_202619_track1"

class ReviewDocumentRequest(BaseModel):
    research_question: str
    document: str
    template_id: str = "nh_202619_track1"
    plan: dict = Field(default_factory=dict)


# ── Endpoints ──

@router.get("/templates")
async def get_templates():
    """List all available document templates."""
    templates = list_templates()
    return {"templates": [{"id": t.template_id, "name": t.name, "description": t.description} for t in templates]}


@router.get("/templates/{template_id}")
async def get_template_detail(template_id: str):
    """Get detailed template specification."""
    try:
        tpl = get_template(template_id)
        return {
            "template_id": tpl.template_id,
            "name": tpl.name,
            "description": tpl.description,
            "sections": [
                {
                    "section_id": s.section_id,
                    "title_cn": s.title_cn,
                    "title_en": s.title_en,
                    "required_elements": s.required_elements,
                    "min_words": s.min_words,
                    "max_words": s.max_words,
                    "multimodal_hints": s.multimodal_hints,
                    "writing_priority": s.writing_priority,
                }
                for s in tpl.sections
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/generate")
async def generate_document(req: GenerateRequest):
    """Generate a complete document from research question and context."""
    logger.info(f"[API] Document generation requested: template={req.template_id}")
    try:
        engine = DocumentEngine()
        result = await engine.generate_document(
            research_question=req.research_question,
            context=req.context,
            template_id=req.template_id,
        )
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Document generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/section")
async def review_section(req: ReviewSectionRequest):
    """Review a single section for quality and compliance."""
    try:
        tpl = get_template(req.template_id)
        spec = None
        for s in tpl.sections:
            if s.section_id == req.section_id:
                spec = s
                break
        reviewer = SectionReviewerAgent()
        result = await reviewer.run(
            research_question=req.research_question,
            context=req.context,
            section_id=req.section_id,
            section_content=req.section_content,
            section_spec=spec,
        )
        return {"success": result.success, "review": result.output}
    except Exception as e:
        logger.error(f"[API] Section review error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/document")
async def review_document(req: ReviewDocumentRequest):
    """Review a complete document for overall quality."""
    try:
        reviewer = DocumentReviewerAgent()
        result = await reviewer.run(
            research_question=req.research_question,
            context="",
            document=req.document,
            template_id=req.template_id,
            plan=req.plan,
        )
        return {"success": result.success, "review": result.output}
    except Exception as e:
        logger.error(f"[API] Document review error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))