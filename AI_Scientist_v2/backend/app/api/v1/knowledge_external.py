"""智研星枢 - 外部资料采集API（5源搜索 + 导入 + 多线程）"""
import asyncio, logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import User
from app.api.deps import get_current_user
from app.services.external_collector import (
    multi_source_search, fetch_url_content, batch_fetch_urls,
    import_external_to_knowledge, search_semantic_scholar, search_arxiv,
    search_openalex, search_crossref, search_europepmc
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge/external", tags=["外部资料采集"])

@router.get("/search")
async def search_external(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    sources: str = Query(default="semantic_scholar,arxiv,openalex,crossref,europepmc", description="数据源"),
    limit: int = Query(default=10, ge=1, le=50),
    year_from: int = Query(default=None, description="起始年份"),
    user: User = Depends(get_current_user),
):
    """5源并发搜索外部学术资料"""
    source_list = [s.strip() for s in sources.split(",")]
    return await multi_source_search(q, source_list, limit)

@router.post("/fetch-url")
async def fetch_single_url(body: dict, user: User = Depends(get_current_user)):
    url = body.get("url","").strip()
    if not url: raise HTTPException(400, "缺少url参数")
    if not url.startswith(("http://","https://")): raise HTTPException(400, "URL必须以http(s)://开头")
    result = await fetch_url_content(url)
    if "error" in result: raise HTTPException(400, result["error"])
    return result

@router.post("/fetch-urls-batch")
async def fetch_urls_batch(body: dict, user: User = Depends(get_current_user)):
    urls = body.get("urls",[])
    if not urls or not isinstance(urls,list): raise HTTPException(400, "需要提供urls列表")
    if len(urls)>10: raise HTTPException(400, "单次最多10个URL")
    return {"results": await batch_fetch_urls(urls), "total": len(urls)}

@router.post("/import")
async def import_paper(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    paper = body.get("paper")
    if not paper: raise HTTPException(400, "缺少paper数据")
    return await import_external_to_knowledge(db, user.id, paper, body.get("save_path"))

@router.post("/import-batch")
async def import_papers_batch(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    papers = body.get("papers",[])
    if not papers: raise HTTPException(400, "缺少papers列表")
    if len(papers)>20: raise HTTPException(400, "单次最多20篇")
    sem = asyncio.Semaphore(5)
    async def _imp(p):
        async with sem:
            try: return await import_external_to_knowledge(db, user.id, p)
            except Exception as e: return {"error":str(e),"title":p.get("title","?")}
    results = await asyncio.gather(*[_imp(p) for p in papers])
    return {"imported": sum(1 for r in results if "error" not in r), "total": len(papers), "results": list(results)}
