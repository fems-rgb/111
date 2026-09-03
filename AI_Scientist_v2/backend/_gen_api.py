import pathlib

BASE = pathlib.Path('backend/app')
NL = chr(10)
TQ = chr(34) * 3

def w(rel, content):
    p = BASE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    print(f'  wrote {p} ({len(content)} bytes)')

print('Generating api/v1/documents.py ...')

lines = []
lines.append(TQ + 'Document Engine API - document generation and review endpoints' + TQ)
lines.append('import logging')
lines.append('from typing import Optional')
lines.append('from fastapi import APIRouter, HTTPException')
lines.append('from pydantic import BaseModel, Field')
lines.append('from app.services.doc_engine import DocumentEngine')
lines.append('from app.agents.doc_reviewer import SectionReviewerAgent, DocumentReviewerAgent')
lines.append('from app.contracts.document_template import get_template, list_templates')
lines.append('')
lines.append('logger = logging.getLogger(__name__)')
lines.append('router = APIRouter(prefix="/documents", tags=["documents"])')
lines.append('')
lines.append('')
lines.append('# ── Request/Response Models ──')
lines.append('')
lines.append('class GenerateRequest(BaseModel):')
lines.append('    research_question: str = Field(..., description="\u7814\u7a76\u95ee\u9898")')
lines.append('    context: str = Field(default="", description="\u7814\u7a76\u80cc\u666f/\u4e0a\u4e0b\u6587")')
lines.append('    template_id: str = Field(default="nh_202619_track1", description="\u6587\u6863\u6a21\u677fID")')
lines.append('')
lines.append('class ReviewSectionRequest(BaseModel):')
lines.append('    research_question: str')
lines.append('    context: str = ""')
lines.append('    section_id: str')
lines.append('    section_content: str')
lines.append('    template_id: str = "nh_202619_track1"')
lines.append('')
lines.append('class ReviewDocumentRequest(BaseModel):')
lines.append('    research_question: str')
lines.append('    document: str')
lines.append('    template_id: str = "nh_202619_track1"')
lines.append('    plan: dict = Field(default_factory=dict)')
lines.append('')
lines.append('')
lines.append('# ── Endpoints ──')
lines.append('')
lines.append('@router.get("/templates")')
lines.append('async def get_templates():')
lines.append('    """List all available document templates."""')
lines.append('    templates = list_templates()')
lines.append('    return {"templates": [{"id": t.template_id, "name": t.name, "description": t.description} for t in templates]}')
lines.append('')
lines.append('')
lines.append('@router.get("/templates/{template_id}")')
lines.append('async def get_template_detail(template_id: str):')
lines.append('    """Get detailed template specification."""')
lines.append('    try:')
lines.append('        tpl = get_template(template_id)')
lines.append('        return {')
lines.append('            "template_id": tpl.template_id,')
lines.append('            "name": tpl.name,')
lines.append('            "description": tpl.description,')
lines.append('            "sections": [')
lines.append('                {')
lines.append('                    "section_id": s.section_id,')
lines.append('                    "title_cn": s.title_cn,')
lines.append('                    "title_en": s.title_en,')
lines.append('                    "required_elements": s.required_elements,')
lines.append('                    "min_words": s.min_words,')
lines.append('                    "max_words": s.max_words,')
lines.append('                    "multimodal_hints": s.multimodal_hints,')
lines.append('                    "writing_priority": s.writing_priority,')
lines.append('                }')
lines.append('                for s in tpl.sections')
lines.append('            ],')
lines.append('        }')
lines.append('    except ValueError as e:')
lines.append('        raise HTTPException(status_code=404, detail=str(e))')
lines.append('')
lines.append('')
lines.append('@router.post("/generate")')
lines.append('async def generate_document(req: GenerateRequest):')
lines.append('    """Generate a complete document from research question and context."""')
lines.append('    logger.info(f"[API] Document generation requested: template={req.template_id}")')
lines.append('    try:')
lines.append('        engine = DocumentEngine()')
lines.append('        result = await engine.generate_document(')
lines.append('            research_question=req.research_question,')
lines.append('            context=req.context,')
lines.append('            template_id=req.template_id,')
lines.append('        )')
lines.append('        if not result["success"]:')
lines.append('            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))')
lines.append('        return result')
lines.append('    except HTTPException:')
lines.append('        raise')
lines.append('    except Exception as e:')
lines.append('        logger.error(f"[API] Document generation error: {e}", exc_info=True)')
lines.append('        raise HTTPException(status_code=500, detail=str(e))')
lines.append('')
lines.append('')
lines.append('@router.post("/review/section")')
lines.append('async def review_section(req: ReviewSectionRequest):')
lines.append('    """Review a single section for quality and compliance."""')
lines.append('    try:')
lines.append('        tpl = get_template(req.template_id)')
lines.append('        spec = None')
lines.append('        for s in tpl.sections:')
lines.append('            if s.section_id == req.section_id:')
lines.append('                spec = s')
lines.append('                break')
lines.append('        reviewer = SectionReviewerAgent()')
lines.append('        result = await reviewer.run(')
lines.append('            research_question=req.research_question,')
lines.append('            context=req.context,')
lines.append('            section_id=req.section_id,')
lines.append('            section_content=req.section_content,')
lines.append('            section_spec=spec,')
lines.append('        )')
lines.append('        return {"success": result.success, "review": result.output}')
lines.append('    except Exception as e:')
lines.append('        logger.error(f"[API] Section review error: {e}", exc_info=True)')
lines.append('        raise HTTPException(status_code=500, detail=str(e))')
lines.append('')
lines.append('')
lines.append('@router.post("/review/document")')
lines.append('async def review_document(req: ReviewDocumentRequest):')
lines.append('    """Review a complete document for overall quality."""')
lines.append('    try:')
lines.append('        reviewer = DocumentReviewerAgent()')
lines.append('        result = await reviewer.run(')
lines.append('            research_question=req.research_question,')
lines.append('            context="",')
lines.append('            document=req.document,')
lines.append('            template_id=req.template_id,')
lines.append('            plan=req.plan,')
lines.append('        )')
lines.append('        return {"success": result.success, "review": result.output}')
lines.append('    except Exception as e:')
lines.append('        logger.error(f"[API] Document review error: {e}", exc_info=True)')
lines.append('        raise HTTPException(status_code=500, detail=str(e))')

w('api/v1/documents.py', NL.join(lines))
print('documents.py done')


# === Register router in main.py ===
print('Registering router in main.py ...')
main_py = BASE / 'main.py'
content = main_py.read_text(encoding='utf-8')

# Add import
import_line = 'from app.api.v1 import auth, projects, agents, chat, observability, admin, stream, multimodal, knowledge, skills, automation, knowledge_external, export, batch_run, team, questions, evidence'
new_import_line = import_line + ', documents'

if 'documents' not in content:
    content = content.replace(import_line, new_import_line)
    
    # Find last include_router line and add after it
    last_include = 'app.include_router(evidence.router, prefix="/api/v1")'
    if last_include in content:
        content = content.replace(
            last_include,
            last_include + NL + 'app.include_router(documents.router, prefix="/api/v1")'
        )
    else:
        # Fallback: find any include_router and append after the last one
        lines_list = content.split(NL)
        insert_idx = -1
        for i, line in enumerate(lines_list):
            if 'include_router' in line and 'prefix="/api/v1"' in line:
                insert_idx = i
        if insert_idx >= 0:
            lines_list.insert(insert_idx + 1, 'app.include_router(documents.router, prefix="/api/v1")')
            content = NL.join(lines_list)
    
    main_py.write_text(content, encoding='utf-8')
    print('  main.py updated with documents router')
else:
    print('  documents router already registered')

print('API integration complete!')
