"""课件版面设计系统 —— 让 AI 生成的课件具备「答辩级」版式

问题背景：旧实现用 python-pptx 默认母版（标题 + 项目符号）导出，
网页配图也只是白底加一条蓝线再堆要点，逐页观感是「一坨文字」，
和网上优秀答辩 PPT（一页一个论点、留白、视觉层级、章节导航）差距很大。

本模块把「内容」与「版式」彻底分开：
1. 内容层由 LLM 按 layout 语义产出（kicker / lead / bullets / cards / metrics / compare）；
2. 版式层在这里统一渲染。网页配图（Pillow）与导出 pptx（python-pptx）共用同一套
   设计 token 与 12 列网格，保证「网页看到的」与「下载到的」视觉一致。

版式清单：
  cover    封面（深色满版）
  section  章节过渡页（大编号 + 本章关键问题）
  bullets  论点页（一页一个观点，主点 + 子点 + 「讲透」侧栏）
  cards    卡片页（2×2 / 3 列）
  compare  对比页（左右双栏）
  metric   数据页（2~3 个大数字）
  chart    图表页（柱状 / 条形 / 折线）
  flow     流程图页（2~4 步，带箭头）
  split    图文分栏页（左要点 + 右图）
  quote    金句页
  table    表格页
  end      结课页
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# ── 设计 token（网页图与 pptx 共用）────────────────────────────
INK = "#0F172A"        # 主文字 / 深色底
INK_SOFT = "#1E293B"
MUTED = "#475569"      # 次级文字
FAINT = "#94A3B8"      # 辅助信息
LINE = "#E2E8F0"       # 分隔线
BG_SOFT = "#F8FAFC"    # 浅底
BRAND = "#4338CA"      # 主色（靛蓝，学术答辩常用）
BRAND_LIGHT = "#EEF2FF"
BRAND_MID = "#818CF8"
ACCENT = "#0891B2"     # 次强调（青）
ACCENT_LIGHT = "#ECFEFF"
WARM = "#B45309"
WARM_LIGHT = "#FFFBEB"
WHITE = "#FFFFFF"

CARD_TINTS = [
    ("#EEF2FF", BRAND),
    ("#ECFEFF", ACCENT),
    ("#FFFBEB", WARM),
    ("#F1F5F9", MUTED),
]

LAYOUTS = ("cover", "section", "bullets", "cards", "compare", "metric",
           "chart", "flow", "split", "quote", "table", "end")

# 画布：1280×720（16:9），pptx 用 13.333×7.5 英寸
W, H = 1280, 720
MARGIN_X = 88
CONTENT_TOP = 236
CONTENT_BOTTOM = H - 92
FOOTER_Y = H - 52


def _s(v: Any, limit: int = 0) -> str:
    """安全取字符串（去首尾空白，可按字数截断）"""
    t = str(v or "").strip()
    if limit and len(t) > limit:
        t = t[: limit - 1].rstrip("，,、;；。.") + "…"
    return t


CHART_TYPES = ("bar", "hbar", "line")


def _num(v: Any) -> float:
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _chart(slide: dict) -> dict | None:
    """数据图：labels 与 values 对齐后才能画，否则整页空白"""
    c = slide.get("chart")
    if not isinstance(c, dict):
        return None
    labels = [_s(x, 12) for x in (c.get("labels") or [])[:7]]
    vals = [_num(v) for v in (c.get("values") or [])[:7]]
    n = min(len(labels), len(vals))
    # 负值/全零画不出有意义的柱，退回到要点页比画错图好
    if n < 2 or min(vals) < 0:
        return None
    ctype = _s(c.get("type")).lower()
    return {
        "type": ctype if ctype in CHART_TYPES else "bar",
        "labels": labels[:n], "values": vals[:n],
        "unit": _s(c.get("unit"), 8),
        "caption": _s(c.get("caption"), 44),
        "series_name": _s(c.get("series_name") or c.get("name"), 20),
    }


def _steps(slide: dict) -> list[dict]:
    """流程/结构图：2-4 步，标题必须有"""
    out = []
    for st in (slide.get("steps") or [])[:4]:
        if not isinstance(st, dict):
            continue
        title = _s(st.get("title"), 16)
        if title:
            out.append({"title": title, "desc": _s(st.get("desc"), 46)})
    return out


def infer_layout(slide: dict) -> str:
    """推断版式：优先用 LLM 给的 layout，其次按内容形态兜底。

    历史课件没有 layout 字段，靠这里保证老数据也能套上新版式而不是退回堆字。
    """
    raw = _s(slide.get("layout")).lower()
    if raw in LAYOUTS:
        # 只有真的带了对应内容才采用，避免空卡片/空图表页
        if raw == "cards" and not slide.get("cards"):
            return "bullets"
        if raw == "metric" and not slide.get("metrics"):
            return "bullets"
        if raw == "compare" and not slide.get("compare"):
            return "bullets"
        if raw == "table" and not slide.get("tables"):
            return "bullets"
        if raw == "chart" and not _chart(slide):
            return "bullets"
        if raw == "flow" and not _steps(slide):
            return "bullets"
        if raw == "split" and not (slide.get("bullets") and (_chart(slide) or _steps(slide))):
            return "bullets"
        return raw
    if slide.get("tables"):
        return "table"
    if _chart(slide):
        return "chart"
    if _steps(slide):
        return "flow"
    if slide.get("metrics"):
        return "metric"
    if slide.get("cards"):
        return "cards"
    if slide.get("compare"):
        return "compare"
    return "bullets"


def _bullets(slide: dict) -> list[dict]:
    """规整要点：最多 8 条（含子点），主点 32 字、子点 42 字内

    旧版只允许 4 条 46 字，页面读起来「一页没多少东西」，课堂讲不透；
    现在允许子点补「为什么/怎么做」，但逐条限长，避免退化成字墙。
    超过 6 条时渲染层会自动缩字号并限为单行，不会叠字。
    """
    out = []
    for b in (slide.get("bullets") or []):
        if isinstance(b, dict):
            lvl = min(int(b.get("level", 0) or 0), 1)
            txt = _s(b.get("text"), 42 if lvl else 32)
        else:
            txt, lvl = _s(b, 32), 0
        if txt:
            out.append({"text": txt, "level": lvl})
        if len(out) >= 8:
            break
    return out


def _detail_bullets(detail: str) -> list[dict]:
    """图/表数据缺失时的兑底：把「讲透」段落切成 3-4 个要点

    模型有时交出无效 chart（负值/标签与数值不匹配），版式会退回 bullets，
    而这一页本来就没有 bullets，结果只剩一句 lead —— 「标题 + 一行字」看着像空页。
    把已有的 detail 拆成要点，宁可少一张图，也不要交一整页空白。
    """
    out = []
    for seg in re.split(r"[。；;!?！？]\s*", (detail or "").strip()):
        seg = seg.strip(" ，,、")
        if len(seg) < 8:
            continue
        if len(seg) > 40:  # 优先在逗号处收口，避免把词切断
            cut = max(seg.rfind("，", 0, 40), seg.rfind("、", 0, 40))
            seg = seg[:cut] if cut >= 14 else seg[:40]
        out.append({"text": seg, "level": 0})
        if len(out) >= 4:
            break
    return out


def _cards(slide: dict) -> list[dict]:
    out = []
    for c in (slide.get("cards") or [])[:4]:
        if not isinstance(c, dict):
            continue
        title = _s(c.get("title"), 14)
        if title:
            out.append({"title": title, "desc": _s(c.get("desc"), 40)})
    return out


def _metrics(slide: dict) -> list[dict]:
    out = []
    for m in (slide.get("metrics") or [])[:3]:
        if not isinstance(m, dict):
            continue
        val = _s(m.get("value"), 10)
        if val:
            out.append({"value": val, "unit": _s(m.get("unit"), 6),
                        "label": _s(m.get("label"), 20)})
    return out


def _compare(slide: dict) -> dict | None:
    c = slide.get("compare")
    if not isinstance(c, dict):
        return None
    left, right = c.get("left") or {}, c.get("right") or {}
    if not (left or right):
        return None
    return {
        "left": {"title": _s(left.get("title"), 16),
                 "items": [_s(i, 32) for i in (left.get("items") or [])[:4] if _s(i)]},
        "right": {"title": _s(right.get("title"), 16),
                  "items": [_s(i, 32) for i in (right.get("items") or [])[:4] if _s(i)]},
    }


def page_parts(slide: dict) -> dict:
    """抽出渲染所需的全部字段（两种渲染器共用，保证语义一致）"""
    parts = {
        "layout": infer_layout(slide),
        "kicker": _s(slide.get("kicker"), 12),
        "title": _s(slide.get("title") or slide.get("chapter"), 30) or "未命名页",
        "lead": _s(slide.get("lead"), 52),
        "bullets": _bullets(slide),
        "cards": _cards(slide),
        "metrics": _metrics(slide),
        "compare": _compare(slide),
        "chart": _chart(slide),
        "steps": _steps(slide),
        "detail": _s(slide.get("detail"), 160),
        "example": _s(slide.get("example"), 90),
        "quote": _s(slide.get("quote") or slide.get("lead"), 60),
        "quote_by": _s(slide.get("quote_by"), 48),
        "takeaway": [_s(t, 24) for t in (slide.get("takeaway") or [])[:3] if _s(t)],
        "tables": (slide.get("tables") or [])[:1],
        "chapter": _s(slide.get("chapter"), 24),
        "page_no": int(slide.get("_page_no") or 0),
        "chapter_no": int(slide.get("chapter_no") or 0),
        "key_question": _s(slide.get("key_question"), 40),
    }
    # 没有任何要点也没有图/表时，用细节段落兑底，避免整页只剩一句 lead
    if parts["layout"] not in ("cover", "section", "end", "quote") and not parts["bullets"]:
        parts["bullets"] = _detail_bullets(parts["detail"])
    return parts


# ══════════════════════════════════════════════════════════
#  字体工具（跨平台：Windows 雅黑 → macOS 苹方 → Linux Noto → 兜底）
# ══════════════════════════════════════════════════════════
_FONT_CACHE: dict[tuple[int, bool], Any] = {}


def load_font(size: int, bold: bool = False):
    from PIL import ImageFont
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = []
    if os.name == "nt":
        win = os.environ.get("WINDIR", r"C:\Windows")
        candidates += [os.path.join(win, "Fonts", "msyhbd.ttc" if bold else "msyh.ttc"),
                       os.path.join(win, "Fonts", "simhei.ttf"),
                       os.path.join(win, "Fonts", "simsun.ttc")]
    candidates += [
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            try:
                f = ImageFont.truetype(p, size)
                _FONT_CACHE[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def _tokens(text: str) -> list[str]:
    """切分换行单元：英文单词/数字整体不拆，中文按字（避免 Tran|sformer）"""
    out: list[str] = []
    buf = ""
    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch in "-_./%+&"):
            buf += ch
        else:
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
    if buf:
        out.append(buf)
    return out


def _wrap(draw, text: str, font, max_w: int, max_lines: int = 2) -> list[str]:
    """按像素宽度换行；先按 token 累加，超长单词才退化为逐字"""
    lines: list[str] = []
    cur = ""
    for tok in _tokens(text):
        if tok == "\n":
            lines.append(cur)
            cur = ""
            continue
        if draw.textlength(cur + tok, font=font) <= max_w:
            cur += tok
            continue
        if cur.strip():
            lines.append(cur)
        cur = "" if tok == " " else tok
        # 单个 token 本身就超宽（超长英文词）：逐字切开
        while draw.textlength(cur, font=font) > max_w and len(cur) > 1:
            cut = cur
            while draw.textlength(cut, font=font) > max_w and len(cut) > 1:
                cut = cut[:-1]
            lines.append(cut)
            cur = cur[len(cut):]
        if len(lines) >= max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return [ln for ln in lines if ln.strip()][:max_lines]


def _print_text(draw, xy, text, font, fill, max_w=0, max_lines=2, spacing=8) -> int:
    """画一段可能换行的文字，返回占用高度"""
    if max_w:
        lines = _wrap(draw, text, font, max_w, max_lines)
    else:
        lines = [text]
    x, y = xy
    h = 0
    for ln in lines:
        draw.text((x, y + h), ln, font=font, fill=fill)
        h += int(font.size * 1.42) + spacing
    return h


# ══════════════════════════════════════════════════════════
#  各版式渲染（Pillow，1280×720）
# ══════════════════════════════════════════════════════════
def _draw_cover(draw, p: dict, deck_title: str, subtitle: str, audience: str):
    draw.rectangle([0, 0, W, H], fill=INK)
    # 右侧装饰：同心弧 + 竖排细线，制造「答辩会场」的纵深感
    for r, color in ((430, "#1E293B"), (330, "#243047"), (230, "#2C3A55")):
        draw.ellipse([W - r - 120, H // 2 - r, W - 120 + r, H // 2 + r], outline=color, width=2)
    draw.rectangle([0, 0, 10, H], fill=BRAND_MID)

    t_lines = _wrap(draw, p["title"], load_font(54, True), 1000, 2)
    t_lead = p["lead"] if p["lead"] and p["lead"] != subtitle else ""
    lead_lines = _wrap(draw, t_lead, load_font(22), 900, 2) if t_lead else []
    block_h = 56 + len(t_lines) * 74 + 34 + len(lead_lines) * 36
    ty = max(160, (H - block_h) // 2 + 44)
    draw.text((MARGIN_X, ty), _s(subtitle or "课程课件", 22), font=load_font(22), fill="#A5B4FC")
    y = ty + 56
    for ln in t_lines:
        draw.text((MARGIN_X, y), ln, font=load_font(54, True), fill=WHITE)
        y += 74
    draw.rectangle([MARGIN_X, y + 28, MARGIN_X + 96, y + 34], fill=BRAND_MID)
    if lead_lines:
        _print_text(draw, (MARGIN_X, y + 58), t_lead, load_font(22), "#CBD5E1", 900, 2, 10)

    meta = " · ".join(x for x in [audience, deck_title] if x)
    if meta:
        draw.text((MARGIN_X, H - 132), _s(meta, 46), font=load_font(19), fill=FAINT)
    draw.text((MARGIN_X, H - 96), "智研星枢 · 课程中心", font=load_font(17), fill="#64748B")


def _draw_section(draw, p: dict, deck_title: str):
    draw.rectangle([0, 0, W, H], fill=WHITE)
    draw.rectangle([0, 0, 14, H], fill=BRAND)
    no = f"{p['chapter_no']:02d}" if p["chapter_no"] else "§"
    draw.text((MARGIN_X, 132), no, font=load_font(150, True), fill="#E0E7FF")
    draw.text((MARGIN_X + 6, 316), _s(p["chapter"] or p["title"], 24), font=load_font(46, True), fill=INK)
    if p["key_question"]:
        draw.text((MARGIN_X + 8, 398), "本章要解决", font=load_font(17), fill=BRAND)
        _print_text(draw, (MARGIN_X + 8, 430), p["key_question"], load_font(24), MUTED, W - MARGIN_X - 180, 2)
    draw.rectangle([MARGIN_X + 6, 378, MARGIN_X + 60, 382], fill=BRAND_MID)
    draw.text((MARGIN_X, H - 78), _s(deck_title, 40), font=load_font(16), fill=FAINT)


def _draw_header(draw, p: dict, deck_title: str):
    """内容页统一页头：kicker + 标题 + lead + 分隔线"""
    x = MARGIN_X
    if p["kicker"]:
        draw.rectangle([x, 92, x + 26, 96], fill=BRAND)
        draw.text((x + 38, 82), p["kicker"], font=load_font(16), fill=BRAND)
    title_font = load_font(38 if len(p["title"]) <= 20 else 32, True)
    y = 120
    for ln in _wrap(draw, p["title"], title_font, W - 2 * MARGIN_X, 2):
        draw.text((x, y), ln, font=title_font, fill=INK)
        y += int(title_font.size * 1.34)
    if p["lead"]:
        y = _print_text(draw, (x, y + 8), p["lead"], load_font(19), MUTED,
                  W - 2 * MARGIN_X - 40, 2, 2) + y + 8
    draw.rectangle([x, max(y, 150) + 18, W - MARGIN_X, max(y, 150) + 20], fill=LINE)


def _draw_footer(draw, deck_title: str, page_no: int):
    draw.rectangle([MARGIN_X, FOOTER_Y - 14, W - MARGIN_X, FOOTER_Y - 13], fill=LINE)
    draw.text((MARGIN_X, FOOTER_Y), _s(deck_title, 38), font=load_font(14), fill=FAINT)
    if page_no:
        no = f"{page_no:02d}"
        draw.text((W - MARGIN_X - 26, FOOTER_Y), no, font=load_font(15, True), fill=FAINT)


def _ctext(draw, cx: float, cy: float, text: str, font, fill):
    """以 (cx, cy) 为中心画一行字（序号、柱顶数值、轴标签用）"""
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, cy - font.size * 0.62), text, font=font, fill=fill)


def _nice_max(v: float) -> float:
    """把最大值向上取整到「好看」的刻度（1/1.5/2/2.5/3/4/5/6/8×10^n）"""
    if v <= 0:
        return 1.0
    import math
    exp = math.floor(math.log10(v))
    base = v / (10 ** exp)
    for step in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if base <= step:
            return step * (10 ** exp)
    return 10 ** (exp + 1)


def _fmt_num(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.1f}"


def _draw_chart(draw, chart: dict, box: tuple[int, int, int, int]):
    """柱状 / 条形 / 折线图（pptx 用同一套几何重画，两端一致）"""
    x0, y0, x1, y1 = box
    labels, vals = chart["labels"], chart["values"]
    unit, ctype = chart["unit"], chart["type"]
    vmax = _nice_max(max(vals) or 1)
    cap_h = 26 if chart["caption"] else 0
    if ctype == "hbar":
        gutter = min(160, int((x1 - x0) * 0.32))
        px0, px1 = x0 + gutter, x1 - 76
        py0, py1 = y0 + 10, y1 - cap_h - 10
        row = (py1 - py0) / max(1, len(vals))
        bh = min(36, row * 0.54)
        for i, (lb, v) in enumerate(zip(labels, vals)):
            cy = py0 + row * (i + 0.5)
            bw = max(2, (v / vmax) * (px1 - px0))
            draw.rounded_rectangle([px0, cy - bh / 2, px0 + bw, cy + bh / 2],
                                   radius=5, fill=ACCENT if v == max(vals) else BRAND)
            draw.text((x0, cy - 12), _s(lb, 10), font=load_font(15), fill=INK_SOFT)
            draw.text((px0 + bw + 10, cy - 11), _fmt_num(v) + unit,
                      font=load_font(14, True), fill=MUTED)
    else:
        gutter = 58 if (x1 - x0) > 700 else 48
        px0, px1 = x0 + gutter, x1 - 10
        # 顶部留 30px，让最高柱的数值标还能画在柱子上方
        py0, py1 = y0 + 30, y1 - cap_h - 38
        for i in range(5):
            gy = py1 - (py1 - py0) * i / 4
            draw.rectangle([px0, gy, px1, gy + 1], fill=LINE if 0 < i < 4 else "#CBD5E1")
            draw.text((x0, gy - 9), _fmt_num(vmax * i / 4), font=load_font(13), fill=FAINT)
        n = len(vals)
        slot = (px1 - px0) / n
        pts = []
        for i, (lb, v) in enumerate(zip(labels, vals)):
            cx = px0 + slot * (i + 0.5)
            cy = py1 - (v / vmax) * (py1 - py0)
            pts.append((cx, cy))
            if ctype != "line":
                bw = min(88, slot * 0.46)
                draw.rounded_rectangle([cx - bw / 2, cy, cx + bw / 2, py1], radius=6,
                                       fill=ACCENT if v == max(vals) else BRAND)
            _ctext(draw, cx, max(py0 - 12, cy - 16), _fmt_num(v) + unit,
                   load_font(14, True), BRAND if ctype == "line" else MUTED)
            _ctext(draw, cx, py1 + 20, _s(lb, 8), load_font(13), MUTED)
        if ctype == "line":
            draw.line(pts, fill=BRAND, width=3, joint="curve")
            for cx, cy in pts:
                draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=WHITE, outline=BRAND, width=3)
    if chart["caption"]:
        draw.text((x0, y1 - 20), _s("数据来源：" + chart["caption"], 46), font=load_font(12), fill=FAINT)


def _draw_flow(draw, steps: list[dict], box: tuple[int, int, int, int], vertical: bool = False):
    """流程/机制图：横向卡片 + 箭头，或竖向堆叠（分栏页用）"""
    x0, y0, x1, y1 = box
    n = len(steps)
    if vertical:
        gap = 12
        row = (y1 - y0 - gap * (n - 1)) // max(1, n)
        for i, st in enumerate(steps):
            y = y0 + i * (row + gap)
            tint, accent = CARD_TINTS[i % len(CARD_TINTS)]
            draw.rounded_rectangle([x0, y, x1, y + row], radius=14, fill=tint)
            draw.ellipse([x0 + 16, y + 14, x0 + 46, y + 44], fill=accent)
            _ctext(draw, x0 + 31, y + 29, str(i + 1), load_font(15, True), WHITE)
            draw.text((x0 + 58, y + 12), _s(st["title"], 12), font=load_font(18, True), fill=INK)
            _print_text(draw, (x0 + 58, y + 42), st["desc"], load_font(14), MUTED,
                        x1 - x0 - 74, 2, 3)
        return

    gap = 46 if n <= 3 else 32
    cw = (x1 - x0 - gap * (n - 1)) // max(1, n)
    ch = min(320, y1 - y0)
    cy0 = y0 + (y1 - y0 - ch) // 2
    for i, st in enumerate(steps):
        x = x0 + i * (cw + gap)
        tint, accent = CARD_TINTS[i % len(CARD_TINTS)]
        draw.rounded_rectangle([x, cy0, x + cw, cy0 + ch], radius=18, fill=tint)
        draw.rectangle([x + 24, cy0 + 26, x + 30, cy0 + ch - 26], fill=accent)
        # 内容整体垂直居中，避免卡片下半部大片空白
        tf, df = load_font(21, True), load_font(15)
        t_lines = _wrap(draw, st["title"], tf, cw - 68, 2)
        d_lines = _wrap(draw, st["desc"], df, cw - 68, 4)
        block = 36 + 18 + len(t_lines) * 30 + 8 + len(d_lines) * 24
        top = cy0 + max(26, (ch - block) // 2 - 10)
        draw.ellipse([x + 46, top, x + 82, top + 36], fill=accent)
        _ctext(draw, x + 64, top + 18, str(i + 1), load_font(17, True), WHITE)
        ty = top + 54
        for ln in t_lines:
            draw.text((x + 46, ty), ln, font=tf, fill=INK)
            ty += 30
        ty += 8
        for ln in d_lines:
            draw.text((x + 46, ty), ln, font=df, fill=MUTED)
            ty += 24
        if i < n - 1:
            ax = x + cw + 10
            ay = cy0 + ch // 2
            draw.rectangle([ax - 6, ay - 1, ax + 6, ay + 2], fill=BRAND_MID)
            draw.polygon([(ax + 6, ay - 10), (ax + 22, ay), (ax + 6, ay + 10)], fill=BRAND_MID)


def _draw_bullet_list(draw, items: list[dict], box: tuple[int, int, int, int], size: int = 24):
    """要点列表（全宽与分栏共用）

    条目多时自动缩字号并限行：6 条以内允许折两行，7 条以上只排单行，
    避免 4-6 条主点 + 子点时两行文字压到相邻条目上。
    """
    x0, y0, x1, y1 = box
    n = max(1, len(items))
    row_h = (y1 - y0) // n
    if n >= 7:
        size, max_lines = min(size, 17), 1
    elif n == 6:
        size, max_lines = min(size, 19), 2
    elif n == 5:
        size, max_lines = min(size, 21), 2
    else:
        size, max_lines = min(size, 23), 2
    num = 0
    for i, b in enumerate(items):
        y = y0 + i * row_h
        if i:
            draw.rectangle([x0, y - 1, x1, y], fill=LINE)
        sub = b["level"] >= 1
        if not sub:
            num += 1
            # 序号徽标：比圆点更有答辩 PPT 的秩序感
            draw.rounded_rectangle([x0, y + row_h // 2 - 19, x0 + 38, y + row_h // 2 + 19],
                                   radius=10, fill=BRAND_LIGHT)
            _ctext(draw, x0 + 19, y + row_h // 2, str(num), load_font(17, True), BRAND)
            f = load_font(size, True)
        else:
            draw.rectangle([x0 + 12, y + row_h // 2 - 1, x0 + 26, y + row_h // 2 + 2], fill=BRAND_MID)
            f = load_font(max(13, size - 4))
        lines = _wrap(draw, b["text"], f, x1 - x0 - 76, max_lines)
        lh = int(f.size * 1.42) + 6
        ty = y + row_h // 2 - len(lines) * lh // 2
        for k, ln in enumerate(lines):
            draw.text((x0 + 56, ty + k * lh), ln, font=f, fill=INK if not sub else MUTED)


def _draw_note_panel(draw, p: dict, box: tuple[int, int, int, int]):
    """「讲透这一页」侧栏：核心解释 + 具体案例，让一页课真能讲下去"""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=BG_SOFT)
    x = x0 + 28
    draw.rectangle([x, y0 + 34, x + 26, y0 + 38], fill=BRAND)
    draw.text((x + 38, y0 + 25), "讲透这一页", font=load_font(16), fill=BRAND)
    yy = y0 + 78
    if p["detail"]:
        yy = _print_text(draw, (x, yy), p["detail"], load_font(17), INK_SOFT,
                         x1 - x0 - 56, 9, 9) + yy
    if p["example"]:
        ey = max(yy + 24, y1 - 158)
        draw.rounded_rectangle([x, ey, x1 - 28, y1 - 26], radius=12, fill=WARM_LIGHT)
        draw.text((x + 18, ey + 14), "案例 / 例题", font=load_font(13, True), fill=WARM)
        _print_text(draw, (x + 18, ey + 42), p["example"], load_font(15), "#7C2D12",
                    x1 - x0 - 92, 4, 6)


def _draw_bullets(draw, p: dict):
    items = p["bullets"] or [{"text": p["lead"] or p["title"], "level": 0}]
    if p["detail"] or p["example"]:
        # 左要点 + 右解释栏：一栏讲论点，一栏讲原理与案例
        lw = int((W - 2 * MARGIN_X) * 0.58)
        _draw_bullet_list(draw, items, (MARGIN_X, CONTENT_TOP + 4, MARGIN_X + lw, CONTENT_BOTTOM), 22)
        _draw_note_panel(draw, p, (MARGIN_X + lw + 34, CONTENT_TOP, W - MARGIN_X, CONTENT_BOTTOM))
    else:
        _draw_bullet_list(draw, items, (MARGIN_X, CONTENT_TOP, W - MARGIN_X, CONTENT_BOTTOM), 24)


def _draw_detail_strip(draw, p: dict, top: int):
    """图表/流程页底部结论条：图看完要有解释，否则学生只记得住颜色"""
    if not p["detail"]:
        return
    draw.rectangle([MARGIN_X, top, W - MARGIN_X, top + 1], fill=LINE)
    draw.text((MARGIN_X, top + 12), "讲透", font=load_font(13, True), fill=BRAND)
    _print_text(draw, (MARGIN_X + 44, top + 8), p["detail"], load_font(15), MUTED,
                W - 2 * MARGIN_X - 54, 2, 4)


def _draw_split(draw, p: dict):
    """图文分栏：左侧论点，右侧数据图 / 流程图"""
    lw = int((W - 2 * MARGIN_X) * 0.44)
    items = p["bullets"] or [{"text": p["lead"] or p["title"], "level": 0}]
    _draw_bullet_list(draw, items, (MARGIN_X, CONTENT_TOP + 4, MARGIN_X + lw, CONTENT_BOTTOM), 19)
    box = (MARGIN_X + lw + 40, CONTENT_TOP, W - MARGIN_X, CONTENT_BOTTOM)
    if p["chart"]:
        _draw_chart(draw, p["chart"], box)
    elif p["steps"]:
        _draw_flow(draw, p["steps"], box, vertical=True)


def _draw_cards(draw, p: dict):
    cards = p["cards"]
    n = len(cards)
    cols = 2 if n != 3 else 3
    rows = (n + cols - 1) // cols
    gap = 22
    avail_w = W - 2 * MARGIN_X
    cw = (avail_w - gap * (cols - 1)) // cols
    avail_h = CONTENT_BOTTOM - CONTENT_TOP
    ch = min(340, (avail_h - gap * (rows - 1)) // rows)
    for i, c in enumerate(cards):
        r, col = divmod(i, cols)
        x = MARGIN_X + col * (cw + gap)
        y = CONTENT_TOP + r * (ch + gap)
        tint, accent = CARD_TINTS[i % len(CARD_TINTS)]
        draw.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=tint)
        draw.rectangle([x, y + 26, x + 6, y + ch - 26], fill=accent)
        ty = y + max(26, (ch - 108) // 2)
        draw.text((x + 30, ty), _s(c["title"], 14), font=load_font(26, True), fill=INK)
        _print_text(draw, (x + 30, ty + 48), c["desc"], load_font(19), MUTED, cw - 60, 3, 8)


def _draw_compare(draw, p: dict):
    c = p["compare"] or {"left": {"title": "", "items": []}, "right": {"title": "", "items": []}}
    gap = 26
    cw = (W - 2 * MARGIN_X - gap) // 2
    for i, side in enumerate(("left", "right")):
        data = c[side]
        x = MARGIN_X + i * (cw + gap)
        y = CONTENT_TOP
        h = CONTENT_BOTTOM - CONTENT_TOP
        fill, accent = ("#F1F5F9", MUTED) if side == "left" else (BRAND_LIGHT, BRAND)
        draw.rounded_rectangle([x, y, x + cw, y + h], radius=16, fill=fill)
        draw.text((x + 30, y + 28), _s(data["title"], 16), font=load_font(24, True), fill=INK)
        draw.rectangle([x + 30, y + 70, x + 82, y + 74], fill=accent)
        items = data["items"] or []
        step = max(58, (h - 108) // max(1, len(items)))
        yy = y + 96
        for item in items:
            draw.ellipse([x + 32, yy + 9, x + 41, yy + 18], fill=accent)
            _print_text(draw, (x + 54, yy), item, load_font(18), INK_SOFT, cw - 96, 2, 4)
            yy += step


def _draw_metric(draw, p: dict):
    ms = p["metrics"]
    n = len(ms)
    gap = 20
    cw = (W - 2 * MARGIN_X - gap * (n - 1)) // n
    card_h = CONTENT_BOTTOM - CONTENT_TOP - 4
    for i, m in enumerate(ms):
        x = MARGIN_X + i * (cw + gap)
        draw.rounded_rectangle([x, CONTENT_TOP, x + cw, CONTENT_TOP + card_h], radius=20, fill=BG_SOFT)
        draw.rectangle([x + 30, CONTENT_TOP + 56, x + 92, CONTENT_TOP + 60], fill=BRAND)
        fv = load_font(80, True)
        draw.text((x + 30, CONTENT_TOP + 88), _s(m["value"], 10), font=fv, fill=BRAND)
        if m["unit"]:
            wv = draw.textlength(_s(m["value"], 10), font=fv)
            draw.text((x + 36 + wv, CONTENT_TOP + 128), m["unit"], font=load_font(26, True), fill=BRAND_MID)
        _print_text(draw, (x + 32, CONTENT_TOP + card_h - 118), m["label"], load_font(19), MUTED, cw - 64, 2, 6)


def _draw_quote(draw, p: dict):
    draw.rectangle([MARGIN_X, CONTENT_TOP, MARGIN_X + 6, CONTENT_BOTTOM], fill=BRAND)
    draw.text((MARGIN_X + 34, CONTENT_TOP - 16), "“", font=load_font(96, True), fill="#C7D2FE")
    qf = load_font(32, True)
    qlines = _wrap(draw, p["quote"], qf, W - 2 * MARGIN_X - 90, 3)
    lh = int(32 * 1.42) + 14
    qy = CONTENT_TOP + max(64, (CONTENT_BOTTOM - CONTENT_TOP - len(qlines) * lh - 56) // 2)
    for k, ln in enumerate(qlines):
        draw.text((MARGIN_X + 46, qy + k * lh), ln, font=qf, fill=INK)
    if p["quote_by"]:
        draw.text((MARGIN_X + 48, qy + len(qlines) * lh + 26), "— " + p["quote_by"],
                  font=load_font(18), fill=FAINT)


def _draw_table(draw, p: dict):
    rows = p["tables"][0] if p["tables"] else []
    if not rows:
        return _draw_bullets(draw, p)
    cols = max(len(r) for r in rows)
    rows = [list(r) + [""] * (cols - len(r)) for r in rows[:7]]
    avail_w = W - 2 * MARGIN_X
    cw = avail_w // cols
    head_h = 56
    row_h = min(88, (CONTENT_BOTTOM - CONTENT_TOP - head_h) // max(1, len(rows) - 1))
    for ri, row in enumerate(rows):
        y = CONTENT_TOP + (head_h if ri else 0) + max(0, ri - 1) * row_h
        if ri == 0:
            y = CONTENT_TOP
            draw.rectangle([MARGIN_X, y, MARGIN_X + avail_w, y + head_h], fill=BRAND)
        elif ri % 2 == 0:
            draw.rectangle([MARGIN_X, y, MARGIN_X + avail_w, y + row_h], fill=BG_SOFT)
        for ci, cell in enumerate(row):
            x = MARGIN_X + ci * cw
            f = load_font(17, ri == 0)
            _print_text(draw, (x + 14, y + (head_h if ri == 0 else row_h) // 2 - f.size // 2 - 2),
                        _s(cell, 40), f, WHITE if ri == 0 else INK_SOFT, cw - 28, 1, 0)
    draw.rectangle([MARGIN_X, CONTENT_TOP, MARGIN_X + avail_w, CONTENT_TOP + head_h + row_h * (len(rows) - 1)],
                   outline=LINE, width=1)


def _draw_end(draw, p: dict, deck_title: str):
    draw.rectangle([0, 0, W, H], fill=INK)
    draw.rectangle([0, 0, 10, H], fill=BRAND_MID)
    draw.text((MARGIN_X, 148), "结课", font=load_font(18), fill="#A5B4FC")
    draw.text((MARGIN_X, 190), "谢谢", font=load_font(64, True), fill=WHITE)
    draw.rectangle([MARGIN_X, 292, MARGIN_X + 88, 297], fill=BRAND_MID)
    items = p["takeaway"] or [b["text"] for b in p["bullets"][:3]]
    yy = 340
    for i, t in enumerate(items[:3]):
        draw.text((MARGIN_X, yy), f"0{i + 1}", font=load_font(15, True), fill=BRAND_MID)
        _print_text(draw, (MARGIN_X + 52, yy - 4), t, load_font(21), "#E2E8F0", W - 2 * MARGIN_X - 80, 1, 0)
        yy += 52
    draw.text((MARGIN_X, H - 74), _s(deck_title, 40), font=load_font(16), fill="#64748B")


def render_slide_image(slide: dict, out_abs: str, out_rel: str, name: str,
                       page_no: int = 0, deck_title: str = "", audience: str = "") -> tuple[str, int]:
    """把一页画成 1280×720 的版式化预览图（电子书与阅读器用）"""
    from PIL import Image, ImageDraw
    try:
        p = page_parts({**slide, "_page_no": page_no or slide.get("_page_no", 0)})
        img = Image.new("RGB", (W, H), WHITE)
        draw = ImageDraw.Draw(img)
        layout = p["layout"]
        if layout == "cover":
            _draw_cover(draw, p, deck_title, p["kicker"] or p["lead"], audience)
        elif layout == "section":
            _draw_section(draw, p, deck_title)
        elif layout == "end":
            _draw_end(draw, p, deck_title)
        else:
            _draw_header(draw, p, deck_title)
            if layout == "cards" and p["cards"]:
                _draw_cards(draw, p)
            elif layout == "compare" and p["compare"]:
                _draw_compare(draw, p)
            elif layout == "metric" and p["metrics"]:
                _draw_metric(draw, p)
            elif layout == "chart" and p["chart"]:
                bottom = CONTENT_BOTTOM - (66 if p["detail"] else 0)
                _draw_chart(draw, p["chart"], (MARGIN_X, CONTENT_TOP + 6, W - MARGIN_X, bottom))
                _draw_detail_strip(draw, p, bottom + 6)
            elif layout == "flow" and p["steps"]:
                bottom = CONTENT_BOTTOM - (66 if p["detail"] else 0)
                _draw_flow(draw, p["steps"], (MARGIN_X, CONTENT_TOP + 10, W - MARGIN_X, bottom))
                _draw_detail_strip(draw, p, bottom + 6)
            elif layout == "split":
                _draw_split(draw, p)
            elif layout == "quote":
                _draw_quote(draw, p)
            elif layout == "table" and p["tables"]:
                _draw_table(draw, p)
            else:
                _draw_bullets(draw, p)
            _draw_footer(draw, deck_title, p["page_no"])

        path = os.path.join(out_abs, name)
        from app.services.ppt_service import JPEG_QUALITY
        img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        return os.path.join(out_rel, name).replace("\\", "/"), max(1, os.path.getsize(path) // 1024)
    except Exception as e:
        logger.warning(f"slide image draw failed: {e}")
        return "", 0


# ══════════════════════════════════════════════════════════
#  pptx 导出（与上图共用同一套像素网格，1px = 13.333/1280 英寸）
# ══════════════════════════════════════════════════════════
FONT_NAME = "微软雅黑"


def _emu(px: float):
    from pptx.util import Emu
    return Emu(int(px * 914400 * 13.333 / 1280))


def _rgb(hex_color: str):
    from pptx.dml.color import RGBColor
    return RGBColor.from_string(hex_color.replace("#", "").upper())


def _set_font(run, size: int, bold: bool, color: str):
    """中文字体必须同时设置 latin 与 eastAsia，否则 PowerPoint 会回退到宋体"""
    from pptx.oxml.ns import qn
    from pptx.util import Pt
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)
    run.font.name = FONT_NAME
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            from lxml import etree
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", FONT_NAME)


def _shape(slide, x, y, w, h, fill: str, radius: bool = False, line: str = ""):
    from pptx.enum.shapes import MSO_SHAPE
    st = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(st, _emu(x), _emu(y), _emu(w), _emu(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = _rgb(fill)
    if line:
        shp.line.color.rgb = _rgb(line)
        shp.line.width = _emu(1)
    else:
        shp.line.fill.background()
    try:
        shp.shadow.inherit = False
    except Exception:
        pass
    if radius:
        try:
            shp.adjustments[0] = 0.08
        except Exception:
            pass
    return shp


def _ring(slide, x, y, d: int, color: str):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, _emu(x), _emu(y), _emu(d), _emu(d))
    shp.fill.background()
    shp.line.color.rgb = _rgb(color)
    shp.line.width = _emu(1.5)
    try:
        shp.shadow.inherit = False
    except Exception:
        pass


def _text(slide, x, y, w, h, text: str, size: int = 20, bold: bool = False,
          color: str = INK, align: str = "left", anchor: str = "top",
          line: float = 1.3):
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    box = slide.shapes.add_textbox(_emu(x), _emu(y), _emu(w), _emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE}[anchor]
    p = tf.paragraphs[0]
    p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER,
                   "right": PP_ALIGN.RIGHT}[align]
    p.line_spacing = line
    run = p.add_run()
    run.text = text
    _set_font(run, size, bold, color)
    return box


def _header(slide, p: dict):
    if p["kicker"]:
        _shape(slide, MARGIN_X, 92, 26, 4, BRAND)
        _text(slide, MARGIN_X + 38, 78, 700, 26, p["kicker"], 14, False, BRAND)
    size = 38 if len(p["title"]) <= 20 else 32
    _text(slide, MARGIN_X, 118, W - 2 * MARGIN_X, 120, p["title"], size, True, INK, line=1.24)
    if p["lead"]:
        _text(slide, MARGIN_X, 200, W - 2 * MARGIN_X - 60, 60, p["lead"], 18, False, MUTED)
    _shape(slide, MARGIN_X, 224, W - 2 * MARGIN_X, 1.5, LINE)


def _footer(slide, deck_title: str, page_no: int):
    _shape(slide, MARGIN_X, FOOTER_Y - 14, W - 2 * MARGIN_X, 1, LINE)
    _text(slide, MARGIN_X, FOOTER_Y - 4, 700, 24, _s(deck_title, 38), 12, False, FAINT)
    if page_no:
        _text(slide, W - MARGIN_X - 50, FOOTER_Y - 6, 50, 26, f"{page_no:02d}", 13, True, FAINT, "right")


def _p_cover(slide, p: dict, deck_title: str, audience: str):
    _shape(slide, 0, 0, W, H, INK)
    for r, color in ((430, "#1E293B"), (330, "#243047"), (230, "#2C3A55")):
        _ring(slide, W - r - 120, H // 2 - r, r * 2, color)
    _shape(slide, 0, 0, 10, H, BRAND_MID)
    title = p["title"]
    t_lines = 1 + len(title) // 19
    t_lead = p["lead"] if p["lead"] and p["lead"] != (p["kicker"] or p["lead"]) else ""
    l_lines = 0 if not t_lead else 1 + len(t_lead) // 33
    ty = max(168, (H - (56 + t_lines * 74 + 34 + l_lines * 36)) // 2 + 34)
    _text(slide, MARGIN_X, ty, 860, 30, _s(p["kicker"] or p["lead"] or "课程课件", 22), 19, False, "#A5B4FC")
    _text(slide, MARGIN_X, ty + 50, 980, t_lines * 82, title, 52, True, WHITE, line=1.2)
    y = ty + 56 + t_lines * 74
    _shape(slide, MARGIN_X, y + 26, 96, 5, BRAND_MID)
    if t_lead:
        _text(slide, MARGIN_X, y + 56, 900, l_lines * 34 + 12, t_lead, 19, False, "#CBD5E1", line=1.5)
    meta = " · ".join(x for x in [audience, deck_title] if x)
    if meta:
        _text(slide, MARGIN_X, H - 140, 900, 30, _s(meta, 46), 17, False, FAINT)
    _text(slide, MARGIN_X, H - 102, 600, 26, "智研星枢 · 课程中心", 14, False, "#64748B")


def _p_section(slide, p: dict, deck_title: str):
    _shape(slide, 0, 0, 14, H, BRAND)
    no = f"{p['chapter_no']:02d}" if p["chapter_no"] else "§"
    _text(slide, MARGIN_X, 110, 500, 210, no, 132, True, "#E0E7FF", line=1.0)
    _text(slide, MARGIN_X + 6, 316, W - 2 * MARGIN_X, 70, _s(p["chapter"] or p["title"], 24), 42, True, INK)
    _shape(slide, MARGIN_X + 6, 378, 54, 3, BRAND_MID)
    if p["key_question"]:
        _text(slide, MARGIN_X + 6, 408, 240, 28, "本章要解决", 15, True, BRAND)
        _text(slide, MARGIN_X + 6, 440, W - 2 * MARGIN_X - 160, 90, p["key_question"], 22, False, MUTED, line=1.4)
    _text(slide, MARGIN_X, H - 82, 700, 26, _s(deck_title, 40), 13, False, FAINT)


def _p_bullets(slide, p: dict):
    items = p["bullets"] or [{"text": p["lead"] or p["title"], "level": 0}]
    has_note = bool(p["detail"] or p["example"])
    x1 = MARGIN_X + int((W - 2 * MARGIN_X) * 0.58) if has_note else W - MARGIN_X
    top = CONTENT_TOP + 8
    n = max(1, len(items))
    row_h = (CONTENT_BOTTOM - top) // n
    size = 22 if has_note else 24
    # 与 Pillow 同规则：条目多时缩字号；7 条以上限单行（超长截断），避免文本框溢到下一行
    max_chars = 0
    if n >= 7:
        size, max_chars = min(size, 17), 26
    elif n == 6:
        size = min(size, 19)
    elif n == 5:
        size = min(size, 21)
    num = 0
    for i, b in enumerate(items):
        y = top + i * row_h
        if i:
            _shape(slide, MARGIN_X, y - 1, x1 - MARGIN_X, 1, LINE)
        sub = b["level"] >= 1
        if not sub:
            num += 1
            _shape(slide, MARGIN_X, y + row_h // 2 - 18, 38, 38, BRAND_LIGHT, radius=True)
            _text(slide, MARGIN_X, y + row_h // 2 - 13, 38, 30, str(num), 15, True, BRAND, "center", "middle")
        else:
            _shape(slide, MARGIN_X + 12, y + row_h // 2 - 1, 14, 3, BRAND_MID)
        text = b["text"]
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "…"
        _text(slide, MARGIN_X + 56, y, x1 - MARGIN_X - 70, row_h, text,
              size if not sub else max(12, size - 4), not sub, INK if not sub else MUTED,
              "left", "middle", line=1.35)
    if has_note:
        _p_note_panel(slide, p, (x1 + 34, CONTENT_TOP, W - MARGIN_X, CONTENT_BOTTOM))


def _p_note_panel(slide, p: dict, box):
    """「讲透这一页」侧栏（与 Pillow 版本同位置同层级）"""
    x0, y0, x1, y1 = box
    _shape(slide, x0, y0, x1 - x0, y1 - y0, BG_SOFT, radius=True)
    x = x0 + 28
    _shape(slide, x, y0 + 34, 26, 4, BRAND)
    _text(slide, x + 38, y0 + 22, x1 - x0 - 70, 26, "讲透这一页", 14, False, BRAND)
    yy = y0 + 74
    if p["detail"]:
        h = min(300, (len(p["detail"]) // 22 + 1) * 28 + 8)
        _text(slide, x, yy, x1 - x0 - 56, h, p["detail"], 15, False, INK_SOFT, line=1.55)
        yy += h
    if p["example"]:
        ey = max(yy + 18, y1 - 158)
        _shape(slide, x, ey, x1 - x0 - 56, y1 - 26 - ey, WARM_LIGHT, radius=True)
        _text(slide, x + 18, ey + 12, x1 - x0 - 92, 24, "案例 / 例题", 12, True, WARM)
        _text(slide, x + 18, ey + 38, x1 - x0 - 92, y1 - 26 - ey - 46,
              p["example"], 13, False, "#7C2D12", line=1.4)


def _chart_shapes(slide, chart: dict, box):
    """用形状画柱/条形/折线，与 Pillow 版本几何一致，避开原生图表主题干扰"""
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    x0, y0, x1, y1 = box
    labels, vals = chart["labels"], chart["values"]
    unit, ctype = chart["unit"], chart["type"]
    vmax = _nice_max(max(vals) or 1)
    cap_h = 26 if chart["caption"] else 0
    if ctype == "hbar":
        gutter = min(160, int((x1 - x0) * 0.32))
        px0, px1 = x0 + gutter, x1 - 76
        py0, py1 = y0 + 10, y1 - cap_h - 10
        row = (py1 - py0) / max(1, len(vals))
        bh = min(36, row * 0.54)
        for i, (lb, v) in enumerate(zip(labels, vals)):
            cy = py0 + row * (i + 0.5)
            bw = max(2, (v / vmax) * (px1 - px0))
            _shape(slide, px0, cy - bh / 2, bw, bh, ACCENT if v == max(vals) else BRAND, radius=True)
            _text(slide, x0, cy - 14, gutter - 12, 28, _s(lb, 10), 13, False, INK_SOFT, "left", "middle")
            _text(slide, px0 + bw + 10, cy - 14, 96, 28, _fmt_num(v) + unit, 12, True, MUTED, "left", "middle")
    else:
        gutter = 58 if (x1 - x0) > 700 else 48
        px0, px1 = x0 + gutter, x1 - 10
        # 顶部留 30px，让最高柱的数值标还能画在柱子上方
        py0, py1 = y0 + 30, y1 - cap_h - 38
        for i in range(5):
            gy = py1 - (py1 - py0) * i / 4
            _shape(slide, px0, gy, px1 - px0, 1, LINE if 0 < i < 4 else "#CBD5E1")
            _text(slide, x0, gy - 12, gutter - 8, 24, _fmt_num(vmax * i / 4), 11, False, FAINT, "right", "middle")
        n = len(vals)
        slot = (px1 - px0) / n
        pts = []
        for i, (lb, v) in enumerate(zip(labels, vals)):
            cx = px0 + slot * (i + 0.5)
            cy = py1 - (v / vmax) * (py1 - py0)
            pts.append((cx, cy))
            if ctype != "line":
                bw = min(88, slot * 0.46)
                _shape(slide, cx - bw / 2, cy, bw, py1 - cy, ACCENT if v == max(vals) else BRAND, radius=True)
            _text(slide, cx - slot / 2, max(py0 - 24, cy - 30), slot, 24,
                  _fmt_num(v) + unit, 12, True, BRAND if ctype == "line" else MUTED, "center", "middle")
            _text(slide, cx - slot / 2, py1 + 6, slot, 24, _s(lb, 8), 11, False, MUTED, "center", "middle")
        if ctype == "line":
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                cn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                                _emu(ax), _emu(ay), _emu(bx), _emu(by))
                cn.line.color.rgb = _rgb(BRAND)
                cn.line.width = _emu(3)
            for cx, cy in pts:
                dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, _emu(cx - 5), _emu(cy - 5), _emu(10), _emu(10))
                dot.fill.solid()
                dot.fill.fore_color.rgb = _rgb(WHITE)
                dot.line.color.rgb = _rgb(BRAND)
                dot.line.width = _emu(2.5)
                try:
                    dot.shadow.inherit = False
                except Exception:
                    pass
    if chart["caption"]:
        _text(slide, x0, y1 - 24, x1 - x0, 24, _s("数据来源：" + chart["caption"], 46), 11, False, FAINT)


def _flow_shapes(slide, steps: list[dict], box, vertical: bool = False):
    from pptx.enum.shapes import MSO_SHAPE
    x0, y0, x1, y1 = box
    n = len(steps)
    if vertical:
        gap = 12
        row = (y1 - y0 - gap * (n - 1)) // max(1, n)
        for i, st in enumerate(steps):
            y = y0 + i * (row + gap)
            tint, accent = CARD_TINTS[i % len(CARD_TINTS)]
            _shape(slide, x0, y, x1 - x0, row, tint, radius=True)
            _shape(slide, x0 + 16, y + 14, 30, 30, accent)
            _text(slide, x0 + 16, y + 14, 30, 30, str(i + 1), 13, True, WHITE, "center", "middle")
            _text(slide, x0 + 58, y + 8, x1 - x0 - 74, 26, _s(st["title"], 12), 16, True, INK)
            _text(slide, x0 + 58, y + 36, x1 - x0 - 74, row - 44, st["desc"], 12, False, MUTED, line=1.4)
        return
    gap = 46 if n <= 3 else 32
    cw = (x1 - x0 - gap * (n - 1)) / max(1, n)
    ch = min(360, y1 - y0)
    cy0 = y0 + (y1 - y0 - ch) / 2
    for i, st in enumerate(steps):
        x = x0 + i * (cw + gap)
        tint, accent = CARD_TINTS[i % len(CARD_TINTS)]
        _shape(slide, x, cy0, cw, ch, tint, radius=True)
        _shape(slide, x + 24, cy0 + 26, 6, ch - 52, accent)
        tl = 2 if len(st["title"]) > 11 else 1
        dl = min(4, 1 + len(st["desc"]) // 12)
        block = 36 + 18 + tl * 30 + 8 + dl * 22
        top = cy0 + max(26, (ch - block) / 2 - 10)
        _shape(slide, x + 46, top, 36, 36, accent)
        _text(slide, x + 46, top, 36, 36, str(i + 1), 14, True, WHITE, "center", "middle")
        _text(slide, x + 46, top + 48, cw - 68, tl * 30 + 8, st["title"], 18, True, INK, line=1.3)
        _text(slide, x + 46, top + 48 + tl * 30 + 6, cw - 68, dl * 22 + 6,
              st["desc"], 13, False, MUTED, line=1.5)
        if i < n - 1:
            ax = x + cw + 10
            ay = cy0 + ch / 2 - 10
            arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, _emu(ax - 6), _emu(ay), _emu(28), _emu(20))
            arr.fill.solid()
            arr.fill.fore_color.rgb = _rgb(BRAND_MID)
            arr.line.fill.background()
            try:
                arr.shadow.inherit = False
            except Exception:
                pass


def _p_detail_strip(slide, p: dict, top: int):
    if not p["detail"]:
        return
    _shape(slide, MARGIN_X, top, W - 2 * MARGIN_X, 1, LINE)
    _text(slide, MARGIN_X, top + 8, 44, 24, "讲透", 12, True, BRAND)
    _text(slide, MARGIN_X + 44, top + 6, W - 2 * MARGIN_X - 54, 56, p["detail"],
          13, False, MUTED, line=1.45)


def _p_chart(slide, p: dict):
    bottom = CONTENT_BOTTOM - (66 if p["detail"] else 0)
    _chart_shapes(slide, p["chart"], (MARGIN_X, CONTENT_TOP + 6, W - MARGIN_X, bottom))
    _p_detail_strip(slide, p, bottom + 6)


def _p_flow(slide, p: dict):
    bottom = CONTENT_BOTTOM - (66 if p["detail"] else 0)
    _flow_shapes(slide, p["steps"], (MARGIN_X, CONTENT_TOP + 10, W - MARGIN_X, bottom))
    _p_detail_strip(slide, p, bottom + 6)


def _p_split(slide, p: dict):
    lw = int((W - 2 * MARGIN_X) * 0.44)
    items = p["bullets"] or [{"text": p["lead"] or p["title"], "level": 0}]
    top = CONTENT_TOP + 8
    row_h = (CONTENT_BOTTOM - top) // max(1, len(items))
    num = 0
    for i, b in enumerate(items):
        y = top + i * row_h
        if i:
            _shape(slide, MARGIN_X, y - 1, lw, 1, LINE)
        sub = b["level"] >= 1
        if not sub:
            num += 1
            _shape(slide, MARGIN_X, y + row_h // 2 - 16, 32, 32, BRAND_LIGHT, radius=True)
            _text(slide, MARGIN_X, y + row_h // 2 - 12, 32, 26, str(num), 13, True, BRAND, "center", "middle")
        else:
            _shape(slide, MARGIN_X + 10, y + row_h // 2 - 1, 12, 3, BRAND_MID)
        _text(slide, MARGIN_X + 44, y, lw - 54, row_h, b["text"], 15 if not sub else 12,
              not sub, INK if not sub else MUTED, "left", "middle", line=1.35)
    box = (MARGIN_X + lw + 40, CONTENT_TOP, W - MARGIN_X, CONTENT_BOTTOM)
    if p["chart"]:
        _chart_shapes(slide, p["chart"], box)
    elif p["steps"]:
        _flow_shapes(slide, p["steps"], box, vertical=True)


def _p_cards(slide, p: dict):
    cards = p["cards"]
    n = len(cards)
    cols = 3 if n == 3 else 2
    rows = (n + cols - 1) // cols
    gap = 22
    cw = (W - 2 * MARGIN_X - gap * (cols - 1)) // cols
    ch = min(340, (CONTENT_BOTTOM - CONTENT_TOP - gap * (rows - 1)) // max(1, rows))
    for i, c in enumerate(cards):
        r, col = divmod(i, cols)
        x = MARGIN_X + col * (cw + gap)
        y = CONTENT_TOP + r * (ch + gap)
        tint, accent = CARD_TINTS[i % len(CARD_TINTS)]
        _shape(slide, x, y, cw, ch, tint, radius=True)
        _shape(slide, x, y + 26, 6, ch - 52, accent)
        ty = y + max(26, (ch - 108) // 2)
        _text(slide, x + 30, ty, cw - 60, 34, c["title"], 24, True, INK)
        _text(slide, x + 30, ty + 48, cw - 60, 96, c["desc"], 18, False, MUTED, line=1.45)


def _p_compare(slide, p: dict):
    c = p["compare"] or {"left": {"title": "", "items": []}, "right": {"title": "", "items": []}}
    gap = 26
    cw = (W - 2 * MARGIN_X - gap) // 2
    h = CONTENT_BOTTOM - CONTENT_TOP
    for i, side in enumerate(("left", "right")):
        data = c[side]
        x = MARGIN_X + i * (cw + gap)
        fill, accent = ("#F1F5F9", MUTED) if side == "left" else (BRAND_LIGHT, BRAND)
        _shape(slide, x, CONTENT_TOP, cw, h, fill, radius=True)
        _text(slide, x + 30, CONTENT_TOP + 26, cw - 60, 34, _s(data["title"], 16), 22, True, INK)
        _shape(slide, x + 30, CONTENT_TOP + 68, 52, 4, accent)
        items = data["items"] or []
        step = max(56, (h - 108) // max(1, len(items)))
        yy = CONTENT_TOP + 94
        for item in items:
            _shape(slide, x + 32, yy + 10, 9, 9, accent)
            _text(slide, x + 54, yy, cw - 96, 58, item, 17, False, INK_SOFT, line=1.35)
            yy += step


def _p_metric(slide, p: dict):
    ms = p["metrics"]
    n = len(ms)
    gap = 18
    cw = (W - 2 * MARGIN_X - gap * (n - 1)) // n
    for i, m in enumerate(ms):
        x = MARGIN_X + i * (cw + gap)
        card_h = CONTENT_BOTTOM - CONTENT_TOP - 4
        _shape(slide, x, CONTENT_TOP, cw, card_h, BG_SOFT, radius=True)
        _shape(slide, x + 30, CONTENT_TOP + 56, 62, 4, BRAND)
        _text(slide, x + 30, CONTENT_TOP + 82, cw - 60, 120, m["value"], 62, True, BRAND, line=1.05)
        if m["unit"]:
            _text(slide, x + 30, CONTENT_TOP + 182, cw - 60, 36, m["unit"], 22, True, BRAND_MID)
        _text(slide, x + 30, CONTENT_TOP + card_h - 120, cw - 60, 76, m["label"], 17, False, MUTED, line=1.4)


def _p_quote(slide, p: dict):
    _shape(slide, MARGIN_X, CONTENT_TOP, 6, CONTENT_BOTTOM - CONTENT_TOP, BRAND)
    _text(slide, MARGIN_X + 30, CONTENT_TOP - 26, 120, 120, "“", 84, True, "#C7D2FE", line=1.0)
    qn = 1 + min(2, max(0, len(p["quote"]) // 26 - 1))
    qh = qn * 55
    qy = CONTENT_TOP + max(64, (CONTENT_BOTTOM - CONTENT_TOP - qh - 56) // 2)
    _text(slide, MARGIN_X + 46, qy, W - 2 * MARGIN_X - 96, qh + 20,
          p["quote"], 30, True, INK, line=1.45)
    if p["quote_by"]:
        _text(slide, MARGIN_X + 48, qy + qh + 20, W - 2 * MARGIN_X - 96, 30,
              "— " + p["quote_by"], 16, False, FAINT)


def _p_table(slide, p: dict):
    rows = p["tables"][0] if p["tables"] else []
    if not rows:
        return _p_bullets(slide, p)
    cols = max(len(r) for r in rows)
    rows = [list(r) + [""] * (cols - len(r)) for r in rows[:7]]
    av_w = W - 2 * MARGIN_X
    head_h = 56
    row_h = min(88, (CONTENT_BOTTOM - CONTENT_TOP - head_h) // max(1, len(rows) - 1))
    gt = slide.shapes.add_table(len(rows), cols, _emu(MARGIN_X), _emu(CONTENT_TOP),
                                _emu(av_w), _emu(head_h + row_h * (len(rows) - 1)))
    tbl = gt.table
    tbl.first_row = True
    for ci in range(cols):
        tbl.columns[ci].width = _emu(av_w // cols)
    for ri, row in enumerate(rows):
        tbl.rows[ri].height = _emu(head_h if ri == 0 else row_h)
        for ci, cell_text in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb(BRAND if ri == 0 else (BG_SOFT if ri % 2 == 0 else WHITE))
            cell.margin_left = _emu(12)
            cell.margin_right = _emu(8)
            cell.margin_top = _emu(6)
            cell.margin_bottom = _emu(6)
            from pptx.enum.text import MSO_ANCHOR
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            para = tf.paragraphs[0]
            run = para.add_run()
            run.text = _s(cell_text, 40)
            _set_font(run, 15, ri == 0, WHITE if ri == 0 else INK_SOFT)


def _p_end(slide, p: dict, deck_title: str):
    _shape(slide, 0, 0, W, H, INK)
    _shape(slide, 0, 0, 10, H, BRAND_MID)
    _text(slide, MARGIN_X, 140, 300, 30, "结课", 16, False, "#A5B4FC")
    _text(slide, MARGIN_X, 178, 600, 96, "谢谢", 58, True, WHITE)
    _shape(slide, MARGIN_X, 292, 88, 5, BRAND_MID)
    items = p["takeaway"] or [b["text"] for b in p["bullets"][:3]]
    yy = 336
    for i, t in enumerate(items[:3]):
        _text(slide, MARGIN_X, yy, 40, 26, f"0{i + 1}", 13, True, BRAND_MID)
        _text(slide, MARGIN_X + 52, yy - 6, W - 2 * MARGIN_X - 80, 40, t, 19, False, "#E2E8F0")
        yy += 52
    _text(slide, MARGIN_X, H - 76, 700, 26, _s(deck_title, 40), 13, False, "#64748B")


def render_pptx(slides: list[dict], deck_title: str, out_path: str,
                audience: str = "") -> str:
    """结构化页面 → 16:9 原生 .pptx（不再是默认母版堆项目符号）

    slides 里的 layout / kicker / lead / cards / metrics / compare 字段由
    course_ai_service 产出；历史数据没有这些字段时由 infer_layout 兜底。
    """
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    for idx, raw in enumerate(slides):
        p = page_parts({**raw, "_page_no": raw.get("_page_no") or idx + 1})
        slide = prs.slides.add_slide(blank)
        layout = p["layout"]
        if layout == "cover":
            _p_cover(slide, p, deck_title, audience)
        elif layout == "section":
            _p_section(slide, p, deck_title)
        elif layout == "end":
            _p_end(slide, p, deck_title)
        else:
            _header(slide, p)
            if layout == "cards" and p["cards"]:
                _p_cards(slide, p)
            elif layout == "compare" and p["compare"]:
                _p_compare(slide, p)
            elif layout == "metric" and p["metrics"]:
                _p_metric(slide, p)
            elif layout == "chart" and p["chart"]:
                _p_chart(slide, p)
            elif layout == "flow" and p["steps"]:
                _p_flow(slide, p)
            elif layout == "split":
                _p_split(slide, p)
            elif layout == "quote":
                _p_quote(slide, p)
            elif layout == "table" and p["tables"]:
                _p_table(slide, p)
            else:
                _p_bullets(slide, p)
            _footer(slide, deck_title, p["page_no"])

        if raw.get("notes"):
            try:
                slide.notes_slide.notes_text_frame.text = str(raw["notes"])[:2000]
            except Exception:
                pass

    prs.save(out_path)
    return out_path

