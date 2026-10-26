"""课件派生文档导出 —— 讲义（Word / PDF）与电子书（PDF / EPUB）

网页阅读器、pptx 是「版式化」产物；真正发给学生、印出来带到教室的
是线性文档。这一层把同一份课件内容渲染成 .docx / .pdf / .epub：

- 讲义：按章分组，老师版附讲透/速记/时长，学生版留笔记横线
- 电子书：连贯读物，章节自动分节，PDF 带页码、EPUB 带可跳转目录

所有产物都由 rows（数据库页面 + _deck_extras 版式语义）直接生成，
不依赖网页 DOM，因此离线也能出文件。
"""

from __future__ import annotations

import io
import re
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.services import ppt_service

FONT = "微软雅黑"
INK = RGBColor(0x1F, 0x24, 0x2E)
MUTED = RGBColor(0x5B, 0x63, 0x72)
BRAND = RGBColor(0x37, 0x3F, 0xD8)
WARM = RGBColor(0xB4, 0x53, 0x09)
RISK = RGBColor(0xB9, 0x1C, 0x1C)

CN_NUM = "一二三四五六七八九十"


# ══════════════════════════════════════════════════════════════
#  讲义：结构化中间表示（docx 与 pdf 共用，保证两种格式内容一致）
# ══════════════════════════════════════════════════════════════

def handout_blocks(rows: list[dict], *, title: str, course_title: str = "",
                   version: int = 1, teacher: bool = False, domain: str = "",
                   objectives: list[str] | None = None,
                   exercises: list[str] | None = None,
                   reading: list[str] | None = None,
                   sources: list[str] | None = None) -> list[tuple]:
    """把课件页面摊成讲义块序列。

    块类型：h1 / sub / h2 / h3 / p（cls 区分 detail/example）/ ul / table /
    note（教师速记）/ risk / lines（学生笔记横线）/ meta / pagebreak
    """
    ver = "教师版" if teacher else "学生版"
    meta_bits = [f"课程：{course_title}" if course_title else "", f"课件 v{version}",
                 f"共 {len(rows)} 页", datetime.now().strftime("%Y-%m-%d")]
    if domain:
        meta_bits.append(f"领域：{domain}")

    blocks: list[tuple] = [("h1", f"《{title}》课堂讲义"),
                           ("sub", f"{ver}　·　" + "　·　".join(b for b in meta_bits if b))]

    if objectives:
        blocks.append(("h2", "学习目标"))
        blocks.append(("ul", [(0, str(o)) for o in objectives]))

    # 按章分组：上传型 PPT 没有章节映射时归入「正文」
    grouped: list[tuple[str, list[dict]]] = []
    for r in rows:
        name = str(r.get("chapter") or "正文")
        if grouped and grouped[-1][0] == name:
            grouped[-1][1].append(r)
        else:
            grouped.append((name, [r]))

    heading_i = 0
    for chap, items in grouped:
        # 封面页只是标题重复（标题已印在讲义首页），跳过不留空白页
        if chap in ("封面", "封面页"):
            continue
        # 结课这类过渡页不当章标题，否则会印出「一、封面」
        if chap not in ("结课", "结束", "谢谢"):
            label = CN_NUM[heading_i] if heading_i < len(CN_NUM) else str(heading_i + 1)
            blocks.append(("h2", f"{label}、{chap}"))
            heading_i += 1
        for r in items:
            no = int(r.get("slide_index") or 0) + 1
            blocks.append(("h3", f"第 {no} 页 · {r.get('title') or '（无标题）'}"))

            detail = str(r.get("detail") or "").strip()
            bullets = []
            for b in (r.get("bullets") or []):
                text = str((b or {}).get("text") or "").strip()
                if text:
                    bullets.append((int((b or {}).get("level") or 0), text))
            if bullets:
                blocks.append(("ul", bullets))
            if detail:
                blocks.append(("p", detail, "detail"))

            # 卡片/对比/图表/流程/金句：版式语义摊平（不含 detail/example）
            extra = [(lvl, text) for lvl, text in ppt_service.layout_points(r, include_core=False)
                     if str(text).strip()]
            if extra:
                blocks.append(("ul", extra))

            example = str(r.get("example") or "").strip()
            if example:
                blocks.append(("p", example, "example"))

            # 结课页只有 takeaway，不收进来就只剩一个「谢谢」标题
            takeaways = [str(t).strip() for t in (r.get("takeaway") or []) if str(t).strip()]
            if takeaways:
                blocks.append(("ul", [(0, t) for t in takeaways]))

            for tbl in (r.get("tables") or [])[:1]:
                if tbl and len(tbl) >= 2:
                    blocks.append(("table", [[str(c or "") for c in row] for row in tbl]))

            if teacher:
                if r.get("notes"):
                    blocks.append(("note", str(r["notes"])))
                if float(r.get("risk_score") or 0) >= 0.4:
                    blocks.append(("risk", f"{r.get('risk_category') or '内容陈旧'} — "
                                           f"{r.get('ai_suggestion') or r.get('ai_reason') or ''}"))
            else:
                blocks.append(("lines", 2))
        if teacher:
            blocks.append(("meta", f"本章 {len(items)} 页，建议讲授约 {max(5, len(items) * 3)} 分钟"))
        blocks.append(("pagebreak",))

    if exercises:
        blocks.append(("h2", "课后思考"))
        blocks.append(("ul", [(0, f"{i + 1}. {x}") for i, x in enumerate(exercises)]))
    if reading:
        blocks.append(("h2", "延伸阅读"))
        blocks.append(("ul", [(0, str(x)) for x in reading]))
    if sources:
        blocks.append(("h2", "本次生成所用的素材来源"))
        blocks.append(("ul", [(0, str(s)) for s in sources[:12]]))

    # 结尾的分页符没有意义，去掉
    while blocks and blocks[-1][0] == "pagebreak":
        blocks.pop()
    return blocks


# ── docx 渲染 ────────────────────────────────────────────────

def _set_run(run, *, size: float | None = None, bold: bool | None = None,
             color: RGBColor | None = None, font: str = FONT):
    run.font.name = font
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), font)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color


def _shade(el, fill: str):
    """给段落/单元格加底纹"""
    pr = el.get_or_add_pPr() if hasattr(el, "get_or_add_pPr") else el
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def _para_bottom_border(par, color: str = "D6D9E0"):
    pPr = par._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "6")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _field_page_number(par):
    """插入 PAGE 域，Word 打开后自动显示真实页码"""
    run = par.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    node = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = "1"
    node.append(text)
    fld.append(node)
    run._r.addnext(fld)


def _docx_styles(doc: Document):
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.5)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    normal.paragraph_format.line_spacing = 1.45
    normal.paragraph_format.space_after = Pt(3)
    for name, size, color in (("Heading 1", 20, BRAND), ("Heading 2", 14, INK), ("Heading 3", 11.5, INK)):
        st = doc.styles[name]
        st.font.name = FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = color
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        st.paragraph_format.space_before = Pt(12 if name != "Heading 1" else 0)
        st.paragraph_format.space_after = Pt(6)


def blocks_to_docx(blocks: list[tuple], *, title: str = "") -> bytes:
    doc = Document()
    _docx_styles(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.0)

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run(f"《{title}》课堂讲义　·　第 ")
    _set_run(fr, size=9, color=MUTED)
    _field_page_number(footer)
    tail = footer.add_run(" 页")
    _set_run(tail, size=9, color=MUTED)

    for blk in blocks:
        kind = blk[0]
        if kind == "h1":
            p = doc.add_paragraph(style="Heading 1")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _set_run(p.add_run(str(blk[1])), size=20, bold=True, color=BRAND)
        elif kind == "sub":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _set_run(p.add_run(str(blk[1])), size=9, color=MUTED)
        elif kind == "h2":
            p = doc.add_paragraph(style="Heading 2")
            _set_run(p.add_run(str(blk[1])), size=14, bold=True, color=INK)
        elif kind == "h3":
            p = doc.add_paragraph(style="Heading 3")
            _set_run(p.add_run(str(blk[1])), size=11.5, bold=True, color=INK)
        elif kind == "ul":
            for level, text in blk[1]:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.55 + 0.6 * min(int(level), 2))
                p.paragraph_format.space_after = Pt(1)
                mark = "•" if int(level) == 0 else "–"
                _set_run(p.add_run(f"{mark} "), size=10.5, color=BRAND if level == 0 else MUTED)
                _set_run(p.add_run(str(text)), size=10.5, color=INK if level == 0 else MUTED)
        elif kind == "p":
            cls = blk[2] if len(blk) > 2 else ""
            if cls == "detail":
                p = doc.add_paragraph()
                _set_run(p.add_run("讲透　"), size=9.5, bold=True, color=BRAND)
                _set_run(p.add_run(str(blk[1])), size=10, color=INK)
                _shade(p._p, "F4F6FF")
            elif cls == "example":
                p = doc.add_paragraph()
                _set_run(p.add_run("案例　"), size=9.5, bold=True, color=WARM)
                _set_run(p.add_run(str(blk[1])), size=10, color=RGBColor(0x7C, 0x2D, 0x12))
                _shade(p._p, "FFF8F0")
            else:
                _set_run(doc.add_paragraph().add_run(str(blk[1])), size=10)
        elif kind == "note":
            p = doc.add_paragraph()
            _set_run(p.add_run("讲师速记　"), size=9.5, bold=True, color=WARM)
            _set_run(p.add_run(str(blk[1])), size=9.5, color=MUTED)
            _shade(p._p, "FFFBEB")
        elif kind == "risk":
            p = doc.add_paragraph()
            _set_run(p.add_run("陈旧风险　"), size=9.5, bold=True, color=RISK)
            _set_run(p.add_run(str(blk[1])), size=9.5, color=RISK)
        elif kind == "lines":
            p = doc.add_paragraph()
            _set_run(p.add_run("笔记"), size=9.5, bold=True, color=MUTED)
            for _ in range(max(1, int(blk[1]))):
                line = doc.add_paragraph()
                line.paragraph_format.space_after = Pt(10)
                _para_bottom_border(line)
        elif kind == "table":
            rows = blk[1]
            cols = max(len(r) for r in rows)
            table = doc.add_table(rows=len(rows), cols=cols)
            table.style = "Table Grid"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for ri, row in enumerate(rows):
                for ci in range(cols):
                    cell = table.cell(ri, ci)
                    cell.text = ""
                    run = cell.paragraphs[0].add_run(str(row[ci]) if ci < len(row) else "")
                    _set_run(run, size=9.5, bold=(ri == 0))
                    if ri == 0:
                        _shade(cell._tc.get_or_add_tcPr(), "E8EAF6")
            doc.add_paragraph()
        elif kind == "meta":
            p = doc.add_paragraph()
            _set_run(p.add_run(str(blk[1])), size=9, color=MUTED)
        elif kind == "pagebreak":
            doc.add_page_break()

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── HTML / PDF 渲染（讲义） ──────────────────────────────────

def _esc(text: Any) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


HANDOUT_CSS = """
@page {
  size: A4; margin: 18mm 16mm 16mm 16mm;
  @bottom-center { content: counter(page) " / " counter(pages); font-size: 9pt; color: #8A8F99; }
}
body { font-family: "Microsoft YaHei", "Noto Sans CJK SC", "SimHei", sans-serif;
       font-size: 10.5pt; line-height: 1.75; color: #1F242E; }
h1 { font-size: 20pt; text-align: center; color: #373FD8; margin: 0 0 6px; }
.sub { text-align: center; color: #6B7280; font-size: 9pt; margin-bottom: 18px; }
h2 { font-size: 14pt; margin: 20px 0 8px; padding-left: 8px; border-left: 4px solid #373FD8; }
h3 { font-size: 11.5pt; margin: 14px 0 6px; color: #1F242E; }
ul { margin: 4px 0 6px; padding-left: 20px; }
li { margin: 2px 0; }
li.lv1 { list-style: circle; margin-left: 14px; color: #5B6372; }
.detail { background: #F4F6FF; border-radius: 4px; padding: 6px 10px; margin: 6px 0; }
.detail b, .example b { color: #373FD8; }
.example { background: #FFF8F0; border-radius: 4px; padding: 6px 10px; margin: 6px 0; color: #7C2D12; }
.example b { color: #B45309; }
.note { background: #FFFBEB; border-left: 3px solid #F59E0B; padding: 6px 10px; margin: 6px 0;
        font-size: 9.5pt; color: #5B6372; }
.risk { background: #FEF2F2; border-left: 3px solid #DC2626; padding: 6px 10px; margin: 6px 0;
        font-size: 9.5pt; color: #B91C1C; }
.meta { color: #8A8F99; font-size: 9pt; margin: 5px 0; }
.note-line { border-bottom: 1px solid #D6D9E0; height: 22px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9.5pt; }
th, td { border: 1px solid #D6D9E0; padding: 5px 8px; text-align: left; }
th { background: #E8EAF6; }
.pagebreak { break-after: page; }
"""


def blocks_to_html(blocks: list[tuple], *, subtitle: str = "") -> str:
    out: list[str] = []
    for blk in blocks:
        kind = blk[0]
        if kind == "h1":
            out.append(f"<h1>{_esc(blk[1])}</h1>")
        elif kind == "sub":
            out.append(f'<p class="sub">{_esc(blk[1])}</p>')
        elif kind == "h2":
            out.append(f"<h2>{_esc(blk[1])}</h2>")
        elif kind == "h3":
            out.append(f"<h3>{_esc(blk[1])}</h3>")
        elif kind == "ul":
            items = []
            for level, text in blk[1]:
                cls = ' class="lv1"' if int(level) else ""
                items.append(f"<li{cls}>{_esc(text)}</li>")
            out.append("<ul>" + "".join(items) + "</ul>")
        elif kind == "p":
            cls = blk[2] if len(blk) > 2 else ""
            if cls == "detail":
                out.append(f'<div class="detail"><b>讲透</b>　{_esc(blk[1])}</div>')
            elif cls == "example":
                out.append(f'<div class="example"><b>案例</b>　{_esc(blk[1])}</div>')
            else:
                out.append(f"<p>{_esc(blk[1])}</p>")
        elif kind == "note":
            out.append(f'<div class="note"><b>讲师速记</b>　{_esc(blk[1])}</div>')
        elif kind == "risk":
            out.append(f'<div class="risk"><b>陈旧风险</b>　{_esc(blk[1])}</div>')
        elif kind == "lines":
            out.append('<p class="meta"><b>笔记</b></p>')
            out.append('<div class="note-line"></div>' * max(1, int(blk[1])))
        elif kind == "table":
            rows = blk[1]
            head = "".join(f"<th>{_esc(c)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
        elif kind == "meta":
            out.append(f'<p class="meta">{_esc(blk[1])}</p>')
        elif kind == "pagebreak":
            out.append('<div class="pagebreak"></div>')
    return (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            f"<title>{_esc(subtitle)}</title><style>{HANDOUT_CSS}</style></head>"
            f"<body>{''.join(out)}</body></html>")


def html_to_pdf(html_str: str, out_path: str | Path) -> Path:
    from weasyprint import HTML

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_str).write_pdf(str(path))
    return path


# ══════════════════════════════════════════════════════════════
#  电子书：Markdown → PDF / EPUB
# ══════════════════════════════════════════════════════════════

BOOK_CSS = """
@page {
  size: A4; margin: 22mm 20mm 20mm 20mm;
  @bottom-center { content: counter(page); font-size: 9pt; color: #9AA0A6; }
  @top-center { content: "{{TITLE}}"; font-size: 8.5pt; color: #B0B5BD; }
}
@page :first { @top-center { content: ""; } @bottom-center { content: ""; } }
body { font-family: "Microsoft YaHei", "SimSun", serif;
       font-size: 11pt; line-height: 1.95; color: #22262E; }
h1 { font-size: 26pt; text-align: center; margin: 60mm 0 8mm;
     color: #1F242E; letter-spacing: 1px; }
h2 { font-size: 15pt; margin: 0 0 10px; padding-bottom: 6px; border-bottom: 1px solid #E5E7EB;
     break-before: page; break-after: avoid; }
p { margin: 8px 0; text-align: justify; }
ul { margin: 6px 0 10px; padding-left: 22px; }
li { margin: 3px 0; }
blockquote { margin: 10px 0; padding: 8px 12px; background: #F7F8FA; border-left: 3px solid #C7CBD1;
             color: #5B6372; font-size: 9.5pt; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; }
th, td { border: 1px solid #DDD; padding: 5px 8px; }
th { background: #F3F4F6; }
.cover { text-align: center; margin-top: 30mm; }
.cover .t { font-size: 30pt; font-weight: bold; line-height: 1.4; }
.cover .m { margin-top: 30mm; color: #6B7280; font-size: 10pt; line-height: 2; }
"""


def ebook_html(md_text: str, *, title: str, course_title: str = "",
               slide_count: int = 0) -> str:
    """Markdown 读物 → 书籍排版的 HTML（PDF/EPUB 共用同一套章节切分）"""
    import markdown as md_lib

    chapters = _split_book(md_text, title)
    cover = (f'<div class="cover"><div class="t">{_esc(title)}</div>'
             f'<div class="m">{_esc(course_title) if course_title else "知行 AI 课程"}<br>'
             f'共 {slide_count} 页 · 生成于 {datetime.now().strftime("%Y-%m-%d")}</div></div>'
             f'<div style="break-after:page"></div>')
    body = []
    for head, text in chapters:
        html = md_lib.markdown(text, extensions=["tables", "sane_lists"])
        body.append(html)
    css = BOOK_CSS.replace("{{TITLE}}", _esc(title).replace('"', ""))
    return (f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
            f"<title>{_esc(title)}</title><style>{css}</style></head><body>"
            f"{cover}{''.join(body)}</body></html>")


def _split_book(md_text: str, title: str) -> list[tuple[str, str]]:
    """按 `## ` 切章；第一段（书名/前言）单独成节"""
    parts: list[tuple[str, str]] = []
    head, buf = "", []
    for line in md_text.splitlines():
        if line.startswith("## "):
            if head or buf:
                parts.append((head or title, "\n".join(buf)))
            head, buf = line[3:].strip(), [line]
        else:
            buf.append(line)
    if head or buf:
        parts.append((head or title, "\n".join(buf)))
    # 去掉只有书名的一级标题段落（封面已单独渲染）
    parts = [(h, t) for h, t in parts if t.strip() and not (t.strip().startswith("# ") and len(t.strip()) < 120)]
    return parts or [(title, md_text)]


def _to_xhtml(html: str) -> str:
    """EPUB 要求 XHTML：把 HTML5 的空元素补成自闭合"""
    return re.sub(r"<(br|hr|img|input|meta|link)([^>]*?)\s*/?>", r"<\1\2 />", html)


def build_epub(md_text: str, out_path: str | Path, *, title: str,
               author: str = "知行 AI 课程组", course_title: str = "") -> Path:
    """EPUB3：mimetype + container + nav 目录 + 每章一个 XHTML"""
    import markdown as md_lib

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    chapters = _split_book(md_text, title)
    book_id = f"urn:uuid:{uuid.uuid4()}"

    files: list[tuple[str, str, str]] = []  # (id, 文件名, 章节标题)
    for i, (head, text) in enumerate(chapters, 1):
        files.append((f"ch{i}", f"ch{i}.xhtml", head or f"第 {i} 节"))

    style = """
body { font-family: "Microsoft YaHei", "SimSun", serif; line-height: 1.9; color: #22262E;
       margin: 1.2em; font-size: 1em; }
h1 { font-size: 1.5em; margin: 0 0 0.8em; border-bottom: 1px solid #E5E7EB; padding-bottom: .4em; }
h2 { font-size: 1.2em; margin: 1.2em 0 .6em; }
p { margin: .6em 0; text-align: justify; }
ul { padding-left: 1.2em; } li { margin: .25em 0; }
blockquote { background: #F7F8FA; border-left: 3px solid #C7CBD1; padding: .5em .8em; color: #5B6372;
             font-size: .92em; }
table { border-collapse: collapse; width: 100%; font-size: .9em; }
th, td { border: 1px solid #DDD; padding: .3em .5em; }
"""

    def chapter_xhtml(head: str, text: str) -> str:
        body = _to_xhtml(md_lib.markdown(text, extensions=["tables", "sane_lists"]))
        return ('<?xml version="1.0" encoding="utf-8"?>\n'
                '<!DOCTYPE html>\n'
                '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">'
                f"<head><meta charset=\"utf-8\"/><title>{_esc(head)}</title>"
                '<link rel="stylesheet" type="text/css" href="style.css"/></head>'
                f"<body>{body}</body></html>")

    nav_items = "".join(f'<li><a href="{fn}">{_esc(head)}</a></li>'
                        for _id, fn, head in files)
    nav = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
           '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"'
           ' xml:lang="zh-CN" lang="zh-CN"><head><meta charset="utf-8"/>'
           f'<title>{_esc(title)}</title></head><body>'
           '<nav epub:type="toc" id="toc"><h1>目录</h1><ol>'
           f'{nav_items}</ol></nav></body></html>')

    manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '<item id="css" href="style.css" media-type="text/css"/>']
    spine = ['<itemref idref="nav"/>']
    for _id, fn, _head in files:
        manifest.append(f'<item id="{_id}" href="{fn}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{_id}"/>')

    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           f'<dc:identifier id="bookid">{book_id}</dc:identifier>'
           f"<dc:title>{_esc(title)}</dc:title><dc:language>zh-CN</dc:language>"
           f"<dc:creator>{_esc(author)}</dc:creator>"
           f'<dc:description>{_esc(course_title or title)}</dc:description>'
           f'<meta property="dcterms:modified">{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</meta>'
           f'</metadata><manifest>{"".join(manifest)}</manifest>'
           f'<spine>{"".join(spine)}</spine></package>')

    container = ('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="OEBPS/content.opf"'
                 ' media-type="application/oebps-package+xml"/></rootfiles></container>')

    with zipfile.ZipFile(path, "w") as zf:
        # mimetype 必须是第一个文件且不压缩
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", opf, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav, zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/style.css", style, zipfile.ZIP_DEFLATED)
        for (_id, fn, head), (_h, text) in zip(files, chapters):
            zf.writestr(f"OEBPS/{fn}", chapter_xhtml(head, text), zipfile.ZIP_DEFLATED)
    return path
