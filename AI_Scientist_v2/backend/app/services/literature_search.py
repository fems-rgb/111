# -*- coding: utf-8 -*-
"""文献检索 v3：Crossref 主力 + S2/arXiv 备用"""
import json, re, urllib.parse, urllib.request, time, hashlib, ssl
from pathlib import Path
from typing import List, Dict

CACHE_DIR = Path("output/literature_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

def _cache_get(query):
    key = hashlib.md5(query.encode()).hexdigest()
    p = CACHE_DIR / f"{key}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None

def _cache_set(query, data):
    key = hashlib.md5(query.encode()).hexdigest()
    p = CACHE_DIR / f"{key}.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

def _get(url, timeout=25, retries=3, use_ssl=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, application/xml, text/xml"
    })
    for i in range(retries):
        try:
            ctx = _ssl_ctx if use_ssl else None
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                content_type = r.headers.get("Content-Type", "")
                data = r.read().decode("utf-8")
                if "json" in content_type:
                    return json.loads(data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < retries - 1:
                wait = 2 ** i * 10
                print(f"[literature] 429 限速，等待 {wait}s...")
                time.sleep(wait)
            else:
                if i == retries - 1: print(f"[literature] HTTP {e.code}: {url[:60]}")
                time.sleep(2)
        except Exception as e:
            if i < retries - 1:
                time.sleep(3)
            else:
                print(f"[literature] 连接失败: {e}")
    return None

# ---- Crossref（主力，国内可访问）----
def search_crossref(query, limit=6):
    cached = _cache_get(f"cr:{query}:{limit}")
    if cached:
        print(f"[literature] Crossref 缓存命中 ({len(cached)} 篇)")
        return cached

    out = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.crossref.org/works?query={q}&rows={limit}&select=title,author,published-print,DOI,URL,abstract"
        data = _get(url)
        if not data:
            return out
        for item in data.get("message", {}).get("items", []):
            title = item.get("title", [""])[0] if item.get("title") else ""
            authors = []
            for a in item.get("author", [])[:3]:
                name = f"{a.get('given','')} {a.get('family','')}".strip()
                if name: authors.append(name)
            if len(item.get("author", [])) > 3: authors[-1] += " et al."
            year = ""
            if "published-print" in item:
                y = item["published-print"].get("date-parts", [[""]])[0][0]
                year = str(y) if y else ""
            out.append({
                "title": title, "authors": ", ".join(authors),
                "year": year, "doi": item.get("DOI", ""),
                "url": item.get("URL", ""), "source": "Crossref"
            })
        _cache_set(f"cr:{query}:{limit}", out)
        print(f"[literature] Crossref 检索到 {len(out)} 篇")
    except Exception as e:
        print(f"[literature] Crossref fail: {e}")
    return out

# ---- S2（备用）----
def search_semantic_scholar(query, limit=4):
    cached = _cache_get(f"s2:{query}:{limit}")
    if cached:
        return cached
    out = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit={limit}&fields=title,authors,year,doi,url"
        data = _get(url)
        if not data: return out
        for p in data.get("data", []):
            authors = ", ".join(a["name"] for a in p.get("authors", [])[:3])
            if len(p.get("authors", [])) > 3: authors += " et al."
            out.append({"title": p.get("title",""), "authors": authors,
                        "year": str(p.get("year","")), "doi": p.get("doi",""),
                        "url": p.get("url",""), "source": "SemanticScholar"})
        _cache_set(f"s2:{query}:{limit}", out)
    except: pass
    return out

# ---- arXiv（备用）----
def search_arxiv(query, limit=4):
    cached = _cache_get(f"arxiv:{query}:{limit}")
    if cached:
        return cached
    out = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://export.arxiv.org/api/query?search_query=all:{q}&start=0&max_results={limit}"
        data = _get(url, use_ssl=True)
        if not data: return out
        for e in re.findall(r"<entry>(.*?)</entry>", data, re.S):
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            pu = re.search(r"<published>(.*?)</published>", e, re.S)
            idu = re.search(r"<id>(.*?)</id>", e, re.S)
            au = re.findall(r"<name>(.*?)</name>", e, re.S)
            out.append({"title": t.group(1).strip().replace("\n"," ") if t else "",
                        "authors": ", ".join(au[:3])+(" et al." if len(au)>3 else ""),
                        "year": pu.group(1)[:4] if pu else "", "doi": "",
                        "url": idu.group(1).strip() if idu else "", "source": "arXiv"})
        _cache_set(f"arxiv:{query}:{limit}", out)
    except: pass
    return out

def retrieve_for_project(research_topic, k=8):
    seen, refs = set(), []
    # 1. Crossref 主力
    for r in search_crossref(research_topic, limit=k):
        key = r["title"].lower()[:40]
        if key not in seen: seen.add(key); refs.append(r)
    # 2. S2 补充
    if len(refs) < k:
        for r in search_semantic_scholar(research_topic, limit=k-len(refs)):
            key = r["title"].lower()[:40]
            if key not in seen: seen.add(key); refs.append(r)
    # 3. arXiv 补充
    if len(refs) < k:
        for r in search_arxiv(research_topic, limit=k-len(refs)):
            key = r["title"].lower()[:40]
            if key not in seen: seen.add(key); refs.append(r)
    return refs[:k]

if __name__ == "__main__":
    print("测试检索（dark matter WIMP detection）...")
    r = retrieve_for_project("dark matter WIMP detection", k=3)
    print(f"\n总计检索到 {len(r)} 篇:")
    for x in r:
        print(f"  - {x['title']} ({x['year']}) [{x['source']}]")
