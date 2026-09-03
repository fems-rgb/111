"""智研星枢 - 多源学术搜索（Semantic Scholar + arXiv + OpenAlex + CrossRef + EuropePMC）
单一入口 search_papers()，5源并发 + 单源失败不中断 + title去重 + sources回传"""
import httpx
import logging
import asyncio
from typing import List, Dict, Any
from app.observability.tracer import Tracer

logger = logging.getLogger(__name__)

UA = "AI-Scientist/1.0 (research-bot; mailto:ai-scientist@example.com)"


async def _semantic(q: str, n: int, c: httpx.AsyncClient) -> List[Dict[str, Any]]:
    try:
        r = await c.get("https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": q, "limit": n,
                    "fields": "title,authors,year,abstract,citationCount,url"},
            headers={"User-Agent": UA})
        r.raise_for_status()
        return [{"title": p.get("title",""), 
                 "authors": [a.get("name","") for a in (p.get("authors") or [])[:5]],
                 "year": p.get("year"),
                 "abstract": (p.get("abstract") or "")[:500],
                 "citations": p.get("citationCount",0),
                 "url": p.get("url",""),
                 "source": "semantic_scholar"} for p in (r.json().get("data") or [])]
    except Exception as e:
        logger.warning(f"[Search] semantic_scholar failed: {e}")
        return []


async def _arxiv(q: str, n: int, c: httpx.AsyncClient) -> List[Dict[str, Any]]:
    try:
        r = await c.get("http://export.arxiv.org/api/query",
            params={"search_query": f"all:{q}", "max_results": n,
                    "sortBy": "relevance", "sortOrder": "descending"},
            headers={"User-Agent": UA})
        r.raise_for_status()
        # arXiv Atom XML，简单正则提取（避免引入lxml依赖）
        import re
        entries = re.findall(r"<entry>(.*?)</entry>", r.text, re.S)
        papers = []
        for ent in entries[:n]:
            title = re.search(r"<title>(.*?)</title>", ent, re.S)
            summary = re.search(r"<summary>(.*?)</summary>", ent, re.S)
            published = re.search(r"<published>(\d{4})", ent)
            authors = re.findall(r"<name>(.*?)</name>", ent)
            link = re.search(r'<id>(http://arxiv.org/abs/\S+)</id>', ent)
            if title:
                papers.append({
                    "title": re.sub(r"\s+", " ", title.group(1)).strip(),
                    "authors": authors[:5],
                    "year": int(published.group(1)) if published else None,
                    "abstract": re.sub(r"\s+", " ", summary.group(1)).strip()[:500] if summary else "",
                    "citations": 0,
                    "url": link.group(1) if link else "",
                    "source": "arxiv"})
        return papers
    except Exception as e:
        logger.warning(f"[Search] arxiv failed: {e}")
        return []


async def _openalex(q: str, n: int, c: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """OpenAlex 免费无需key，覆盖2.5亿+作品"""
    try:
        r = await c.get("https://api.openalex.org/works",
            params={"search": q, "per_page": n, "mailto": "ai-scientist@example.com"},
            headers={"User-Agent": UA})
        r.raise_for_status()
        return [{"title": w.get("title",""),
                 "authors": [a.get("author",{}).get("display_name","") for a in (w.get("authorships") or [])[:5]],
                 "year": w.get("publication_year"),
                 "abstract": (w.get("abstract_inverted_index") and _invert_abstract(w["abstract_inverted_index"]))[:500] if w.get("abstract_inverted_index") else "",
                 "citations": w.get("cited_by_count",0),
                 "url": w.get("primary_location",{}).get("landing_page_url","") if w.get("primary_location") else "",
                 "source": "openalex"} for w in (r.json().get("results") or [])]
    except Exception as e:
        logger.warning(f"[Search] openalex failed: {e}")
        return []


def _invert_abstract(idx: dict) -> str:
    """OpenAlex inverted index → plain text"""
    pos_word = []
    for word, positions in idx.items():
        for p in positions:
            pos_word.append((p, word))
    return " ".join(w for _, w in sorted(pos_word))


async def _crossref(q: str, n: int, c: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """CrossRef 免费无需key，覆盖1.5亿+DOI作品"""
    try:
        r = await c.get("https://api.crossref.org/works",
            params={"query": q, "rows": n},
            headers={"User-Agent": UA})
        r.raise_for_status()
        items = r.json().get("message",{}).get("items",[])
        papers = []
        for it in items:
            title = (it.get("title") or [""])[0]
            authors = [f"{a.get('given','')} {a.get('family','')}".strip() for a in (it.get("author") or [])[:5]]
            year = None
            dp = it.get("published-print") or it.get("published-online") or {}
            parts = dp.get("date-parts",[[]])[0]
            if parts: year = parts[0]
            url = it.get("URL","")
            papers.append({"title": title, "authors": authors, "year": year,
                           "abstract": "", "citations": it.get("is-referenced-by-count",0),
                           "url": url, "source": "crossref"})
        return papers
    except Exception as e:
        logger.warning(f"[Search] crossref failed: {e}")
        return []


async def _europepmc(q: str, n: int, c: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """EuropePMC 生物医学文献，免费"""
    try:
        r = await c.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": q, "pageSize": n, "format": "json"},
            headers={"User-Agent": UA})
        r.raise_for_status()
        return [{"title": p.get("title",""),
                 "authors": [a.get("fullName","") for a in (p.get("authorString") and [{"fullName": a} for a in p["authorString"].split(",")] or [])[:5]],
                 "year": p.get("pubYear"),
                 "abstract": (p.get("abstractText") or "")[:500],
                 "citations": p.get("citedByCount",0),
                 "url": f"https://europepmc.org/article/{p['pmcid']}" if p.get("pmcid") else "",
                 "source": "europepmc"} for p in (r.json().get("resultList",{}).get("result") or [])]
    except Exception as e:
        logger.warning(f"[Search] europepmc failed: {e}")
        return []


async def search_papers(query: str, limit: int = 10, project_id: int = None) -> dict:
    span = Tracer.create_span("tool_call", "学术搜索", project_id=project_id)
    span.set_input({"query": query, "limit": limit})
    per_source = max(2, limit // 5 + 1)
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as c:
            results = await asyncio.gather(
                _semantic(query, per_source, c),
                _arxiv(query, per_source, c),
                _openalex(query, per_source, c),
                _crossref(query, per_source, c),
                _europepmc(query, per_source, c),
                return_exceptions=True)
        papers: List[Dict[str, Any]] = []
        sources_ok: List[str] = []
        source_names = ["semantic_scholar","arxiv","openalex","crossref","europepmc"]
        for name, res in zip(source_names, results):
            if isinstance(res, Exception):
                logger.warning(f"[Search] {name} exception: {res}")
                continue
            if res:
                sources_ok.append(name)
                papers.extend(res)
        # title去重（大小写归一）
        seen, dedup = set(), []
        for p in papers:
            k = (p.get("title") or "").strip().lower()
            if k and k not in seen:
                seen.add(k)
                dedup.append(p)
        out = dedup[:limit]
        span.set_output({"count": len(out), "sources": sources_ok})
        Tracer.finish_span(span)
        return {"papers": out, "total": len(out), "sources": sources_ok,
                "error": None if out else "所有源均无结果，请换关键词或检查网络"}
    except Exception as e:
        span.set_error(str(e))
        Tracer.finish_span(span)
        return {"papers": [], "total": 0, "sources": [], "error": str(e)}
