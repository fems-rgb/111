"""智研星枢 - 知识库管理API"""
import os
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database.session import get_db
from app.database.models import User, Document
from app.config import settings
from app.security.sanitizer import sanitize_filename
from app.security.prompt_guard import prompt_guard
from app.api.deps import get_current_user
from app.services.file_parser import parse_research_file
from app.services.knowledge_index import reindex_knowledge_base
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["知识库"])

RESEARCH_FILE_EXTS = {".pdf", ".csv", ".txt", ".md", ".py", ".json", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_RESEARCH_SIZE = 50 * 1024 * 1024


@router.get("")
async def list_documents(
    q: str = Query(default="", description="搜索关键词"),
    ext: str = Query(default="", description="按扩展名过滤"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document).where(Document.user_id == user.id)
    count_stmt = select(func.count()).select_from(Document).where(Document.user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Document.filename.ilike(like)) | (Document.summary.ilike(like)) | (Document.description.ilike(like)))
        count_stmt = count_stmt.where((Document.filename.ilike(like)) | (Document.summary.ilike(like)) | (Document.description.ilike(like)))
    if ext:
        stmt = stmt.where(Document.file_ext == ext)
        count_stmt = count_stmt.where(Document.file_ext == ext)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(desc(Document.created_at)).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {"id": d.id, "filename": d.filename, "file_ext": d.file_ext, "file_size": d.file_size,
         "description": d.description, "summary": d.summary, "parse_status": d.parse_status,
         "tags": d.tags or [], "created_at": d.created_at.isoformat() if d.created_at else ""}
        for d in rows
    ]
    return {"items": items, "total": total}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(default=""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in RESEARCH_FILE_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    content = await file.read()
    if len(content) > MAX_RESEARCH_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，最大允许50MB")
    if description:
        is_safe, reason = prompt_guard.check(description)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"安全检测未通过: {reason}")
    safe_name = sanitize_filename(file.filename or "research_file")
    saved_name = f"{uuid.uuid4().hex[:12]}{ext}"
    save_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user.id}", "research")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, saved_name)
    with open(save_path, "wb") as f:
        f.write(content)
    parsed = await parse_research_file(save_path, file.content_type or "", description)
    doc = Document(
        user_id=user.id, filename=safe_name, saved_name=saved_name, file_ext=ext,
        file_size=len(content), description=description,
        summary=parsed.get("summary", ""), structured_data=parsed.get("data", {}),
        parse_status=parsed.get("status", "error"), tokens_used=parsed.get("tokens", 0),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "file_ext": doc.file_ext,
            "file_size": doc.file_size, "summary": doc.summary,
            "parse_status": doc.parse_status, "tokens_used": doc.tokens_used,
            "created_at": doc.created_at.isoformat() if doc.created_at else ""}


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document).where(Document.id == doc_id, Document.user_id == user.id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    # 安全删除物理文件（saved_name 可能为空或指向目录）
    if doc.saved_name:
        path = os.path.join(settings.UPLOAD_DIR, f"user_{user.id}", "research", doc.saved_name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass  # 文件删除失败不影响数据库记录删除
    await db.delete(doc)
    await db.commit()
    return {"ok": True}



@router.post("/reindex")
async def reindex_knowledge(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """触发知识库重建索引（后台执行）"""
    background_tasks.add_task(reindex_knowledge_base, user.id)
    return {"ok": True, "message": "知识库索引重建已在后台启动"}

@router.get("/stats")
async def knowledge_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count()).select_from(Document).where(Document.user_id == user.id))).scalar() or 0
    by_ext_rows = (await db.execute(select(Document.file_ext, func.count()).where(Document.user_id == user.id).group_by(Document.file_ext))).all()
    by_ext = {r[0]: r[1] for r in by_ext_rows}
    total_size = (await db.execute(select(func.coalesce(func.sum(Document.file_size), 0)).where(Document.user_id == user.id))).scalar() or 0
    return {"total": total, "by_ext": by_ext, "total_size_bytes": total_size}




@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """下载/预览知识库文件"""
    from fastapi.responses import FileResponse

    stmt = select(Document).where(Document.id == doc_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    file_path = getattr(doc, "file_path", None) or os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}", "research", doc.saved_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件物理路径不存在: {file_path}")

    return FileResponse(
        path=file_path,
        filename=getattr(doc, "filename", None) or doc.saved_name,
        media_type="application/octet-stream"
    )


@router.get("/documents/{doc_id}/preview")
async def preview_document(doc_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """预览知识库文件内容（文本类）"""

    stmt = select(Document).where(Document.id == doc_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    # ★ 无物理文件的文档（如AI生成的.meta记录），返回结构化数据
    if not doc.saved_name or doc.file_ext == ".meta":
        sd = doc.structured_data or {}
        return {
            "type": "meta",
            "filename": doc.filename,
            "title": doc.filename,
            "summary": doc.summary or "",
            "structured_data": sd,
            "url": sd.get("url") or sd.get("pdf_url") or "",
            "authors": sd.get("authors", []),
            "year": sd.get("year"),
            "source": sd.get("source", ""),
            "citations": sd.get("citations", 0),
            "doi": sd.get("doi", ""),
            "abstract": sd.get("abstract", ""),
        }

    file_path = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}", "research", doc.saved_name)
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        raise HTTPException(status_code=404, detail=f"文件物理路径不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    text_exts = {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".html", ".xml", ".yaml", ".yml"}

    if ext in text_exts:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(100000)
        return {"content": content, "filename": doc.filename or doc.saved_name, "type": "text"}
    else:
        size = os.path.getsize(file_path)
        return {"content": None, "filename": doc.filename or doc.saved_name, "type": "binary", "size": size, "message": f"二进制文件 ({ext})，请下载后查看"}



@router.get("/{doc_id}/file")
async def serve_doc_file(doc_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """直接返回文档原始文件（用于图片/PDF预览）"""
    from fastapi.responses import FileResponse
    stmt = select(Document).where(Document.id == doc_id, Document.user_id == user.id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    file_path = os.path.join(settings.UPLOAD_DIR, f"user_{user.id}", "research", doc.saved_name)
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    media_types = {
        'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg', 'gif': 'image/gif', 'webp': 'image/webp',
        'svg': 'image/svg+xml', 'bmp': 'image/bmp'
    }
    ext = doc.file_ext.lower().lstrip('.')
    media_type = media_types.get(ext, 'application/octet-stream')
    return FileResponse(str(file_path), media_type=media_type)

@router.get("/search")
async def search_knowledge(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """RAG知识库语义搜索（基于文件名/摘要/描述/结构化数据的全文匹配）"""
    like = f"%{q}%"
    stmt = select(Document).where(
        Document.user_id == user.id,
        (Document.filename.ilike(like))

        | (Document.summary.ilike(like))
        | (Document.description.ilike(like))
        | (Document.structured_data.isnot(None))
    ).order_by(desc(Document.created_at)).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()

    # 对 structured_data 也做内存过滤（SQLite不支持JSON搜索）
    results = []
    for d in rows:
        match_score = 0
        if d.filename and q.lower() in d.filename.lower():
            match_score += 3
        if d.summary and q.lower() in d.summary.lower():
            match_score += 2
        if d.description and q.lower() in d.description.lower():
            match_score += 1
        if d.structured_data:
            sd_text = str(d.structured_data).lower()
            if q.lower() in sd_text:
                match_score += 2
        if match_score > 0 or len(results) < limit:
            results.append({
                "id": d.id,
                "filename": d.filename,
                "summary": (d.summary or "")[:300],
                "file_ext": d.file_ext,
                "tags": d.tags or [],
                "score": match_score,
                "created_at": d.created_at.isoformat() if d.created_at else "",
            })

    # 按匹配分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results[:limit], "total": len(results), "query": q}
