# -*- coding: utf-8 -*-
"""技术方案 Markdown → PDF 生成器

用法：
    python scripts/gen_tech_pdf.py
    python scripts/gen_tech_pdf.py --in ../docs/技术方案.md --out ../docs/技术方案.pdf
    python scripts/gen_tech_pdf.py --maxpages 20

设计：
- markdown → HTML（tables / fenced_code / toc / attr_list）
- A4 portrait · 中文字体（Microsoft YaHei 优先）· 页眉页脚 · 页码
- YAML front matter 自动剥离
- 若指定 --maxpages，生成后校验页数（依赖 pypdf），超出仅打印告警不阻断
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 让脚本无论从哪跑都能 import app.*
_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows GBK
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import markdown  # noqa: E402
from weasyprint import HTML  # noqa: E402

FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)

CSS = """
@page {
    size: A4 portrait;
    margin: 22mm 18mm 20mm 18mm;
    @bottom-left { content: "智研星枢 · AI Scientist v3.0"; font-size: 8pt; color: #777; }
    @bottom-center { content: "挑战杯 XH-202619 技术方案"; font-size: 8pt; color: #777; }
    @bottom-right { content: counter(page) " / " counter(pages); font-size: 8pt; color: #777; }
}
html, body { font-family: "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DengXian", sans-serif;
             font-size: 10.5pt; line-height: 1.55; color: #222; }
h1 { font-size: 22pt; color: #0b3d91; border-bottom: 2.5pt solid #0b3d91;
     padding-bottom: 4pt; margin: 0 0 14pt 0; page-break-before: avoid; }
h2 { font-size: 15pt; color: #0b3d91; border-left: 4pt solid #0b3d91;
     padding-left: 8pt; margin: 20pt 0 8pt 0; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #1a5fb4; margin: 14pt 0 6pt 0; page-break-after: avoid; }
h4 { font-size: 11pt; color: #333; margin: 10pt 0 4pt 0; }
p { margin: 4pt 0; text-align: justify; }
code { font-family: Consolas, "Courier New", monospace; background: #f3f4f6;
       padding: 1pt 3pt; border-radius: 2pt; font-size: 9.5pt; color: #b91c1c; }
pre { background: #1e293b; color: #e2e8f0; padding: 8pt 10pt; border-radius: 4pt;
      overflow-x: auto; font-size: 9pt; page-break-inside: avoid; }
pre code { background: transparent; color: inherit; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th, td { border: 0.6pt solid #cbd5e1; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #f1f5f9; font-weight: bold; color: #0b3d91; }
tr:nth-child(even) td { background: #fafbfc; }
blockquote { border-left: 3pt solid #93c5fd; background: #eff6ff;
             padding: 6pt 10pt; margin: 8pt 0; color: #1e3a8a; }
blockquote p { margin: 2pt 0; }
ul, ol { margin: 4pt 0 4pt 18pt; }
li { margin: 2pt 0; }
hr { border: none; border-top: 1pt dashed #cbd5e1; margin: 12pt 0; }
a { color: #0b3d91; text-decoration: none; }
strong { color: #0b3d91; }
/* 表格中的 ASCII 图保留等宽，用 pre 渲染更佳 */
.ascii-art { font-family: Consolas, "Courier New", monospace; white-space: pre; font-size: 8.5pt; }
/* 首页封面 */
.cover { text-align: center; padding: 40pt 0 20pt 0; page-break-after: always; }
.cover .title { font-size: 26pt; color: #0b3d91; margin: 12pt 0; font-weight: bold; }
.cover .subtitle { font-size: 14pt; color: #475569; margin: 6pt 0; }
.cover .meta { font-size: 11pt; color: #64748b; margin: 4pt 0; }
"""

COVER_HTML = """
<div class="cover">
  <div class="subtitle">挑战杯「揭榜挂帅」专项赛 · 题目 XH-202619</div>
  <div class="title">智研星枢 · AI Scientist v3.0<br/>技术方案</div>
  <div class="subtitle">基于国产开源大模型 Qwen 的多智能体科研假设自动生成平台</div>
  <div class="meta">发榜单位：浙江阿里巴巴云计算有限公司</div>
  <div class="meta">基座模型：通义千问 Qwen（qwen-max / qwen-plus / qwen-vl-max）</div>
  <div class="meta">调用平台：阿里云百炼 DashScope</div>
  <div class="meta">版本：v3.0.0</div>
</div>
"""


def _strip_front_matter(md_text: str) -> tuple[str, dict]:
    """剥离 YAML front matter，返回 (正文, metadata dict)"""
    m = FRONT_MATTER_RE.match(md_text)
    if not m:
        return md_text, {}
    fm_raw = m.group(0)[4:-4]  # 去 --- 分隔
    meta: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return md_text[m.end():], meta


def _fallback_first_h1(md_body: str) -> str:
    """若 markdown 首个标题正好是「智研星枢 · AI Scientist v3.0」，把封面已呈现的内容去掉"""
    lines = md_body.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:])
    return md_body


def md_to_html(md_body: str, meta: dict) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"],
        output_format="html5",
    )
    body_html = md.convert(md_body)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<title>{meta.get('title', '智研星枢 技术方案')}</title>
<style>{CSS}</style>
</head><body>
{COVER_HTML}
{body_html}
</body></html>"""


def gen_pdf(md_path: Path, pdf_path: Path) -> int:
    raw = md_path.read_text(encoding="utf-8")
    body, meta = _strip_front_matter(raw)
    body = _fallback_first_h1(body)
    html = md_to_html(body, meta)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(md_path.parent)).write_pdf(str(pdf_path))
    size_kb = pdf_path.stat().st_size // 1024
    print(f"✅ 已生成 {pdf_path} · {size_kb} KB")
    return _count_pages(pdf_path)


def _count_pages(pdf_path: Path) -> int:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return -1
    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception as e:
        print(f"⚠️ 页数读取失败: {e}")
        return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="技术方案 Markdown → PDF")
    ap.add_argument(
        "--in", dest="src",
        default=str(_BACKEND.parent / "docs" / "技术方案.md"),
        help="输入 markdown 路径",
    )
    ap.add_argument(
        "--out", dest="dst",
        default=str(_BACKEND.parent / "docs" / "技术方案.pdf"),
        help="输出 PDF 路径",
    )
    ap.add_argument("--maxpages", type=int, default=20, help="页数告警阈值（仅提示不阻断）")
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    if not src.exists():
        print(f"❌ 找不到输入文件: {src}", file=sys.stderr)
        return 2

    pages = gen_pdf(src, dst)
    if pages < 0:
        print("ℹ️ 页数未验证（缺 pypdf / PyPDF2）")
    elif pages > args.maxpages:
        print(f"⚠️ 页数 {pages} 超过赛题限制 {args.maxpages}；请精简 技术方案.md")
    else:
        print(f"✅ 页数 {pages} ≤ 阈值 {args.maxpages}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
