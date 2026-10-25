"""课件电子化服务 —— 把 PPTX 拆解成「电子书」

设计动机（对应赛题需求 2）：
1. PPTX 动辄几十 MB，整包下载浏览慢 → 拆解成「文本元数据 + 逐页瘦身分图」，
   首屏只需几十 KB 的 JSON，图片按阅读位置懒加载；
2. PPT 不是好的阅读载体（要点破碎、无连贯正文、无法搜索选中）
   → 提取出真正的文本层（标题/要点/表格/备注），支持选中、搜索、
     并可拼装成连贯的「读物模式」。

同时提供 render_pptx() 反向导出，保证老师课堂投影仍能拿到原生 .pptx。
"""
import io
import os
import logging
from typing import Any

from app.utils import paths

logger = logging.getLogger(__name__)

# 图片瘦身参数：长边上限 + JPEG 质量。1400px 足够全屏阅读，
# 一般可把单页压到 60~180KB。
MAX_IMAGE_EDGE = 1400
JPEG_QUALITY = 78
MIN_IMAGE_BYTES = 8 * 1024  # 小于此说明是装饰图形，不值得单独存


def _slides_dir(courseware_id: int) -> tuple[str, str]:
    """课件渲染图落盘目录：固定根 backend/generated/courseware/…

    返回 (相对 GENERATED_ROOT 的入库路径, 绝对目录)，图片是派生产物不是用户上传，
    因此不再写到 uploads/ 里。
    """
    abs_dir = paths.gen_dir("courseware", f"c{courseware_id // 100 or 1}", f"cw{courseware_id}")
    return paths.rel("courseware", f"c{courseware_id // 100 or 1}", f"cw{courseware_id}"), str(abs_dir)


def _compress_image(blob: bytes, out_abs: str, out_rel: str, name: str) -> tuple[str, int]:
    """内嵌图片重压缩落盘，返回 (相对路径, KB)"""
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(blob))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        w, h = img.size
        scale = min(1.0, MAX_IMAGE_EDGE / max(w, h))
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        path = os.path.join(out_abs, name)
        img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        return os.path.join(out_rel, name).replace("\\", "/"), max(1, os.path.getsize(path) // 1024)
    except Exception as e:
        logger.warning(f"image compress failed: {e}")
        return "", 0


def _extract_text_shapes(slide) -> tuple[str, list[dict], list[list[str]]]:
    """提取标题、要点（带层级）、表格"""
    from pptx.util import Emu
    title = ""
    bullets: list[dict] = []
    tables: list[list[str]] = []

    # 占位符顺序：标题优先
    try:
        if slide.shapes.title is not None:
            title = (slide.shapes.title.text or "").strip()
    except Exception:
        pass

    for shape in slide.shapes:
        # 表格
        if getattr(shape, "has_table", False):
            try:
                rows = []
                for row in shape.table.rows:
                    rows.append([(c.text or "").strip() for c in row.cells])
                tables.append(rows)
            except Exception:
                pass
            continue
        # 文本框
        if not getattr(shape, "has_text_frame", False):
            continue
        # 跳过标题占位符（idx==0）——注意 slide.shapes.title 每次访问返回新代理对象，
        # 用 `is` 比较永假，必须按 placeholder idx 判定
        if _is_title_placeholder(shape):
            continue
        tf = shape.text_frame
        for para in tf.paragraphs:
            text = (para.text or "").strip()
            if not text:
                continue
            level = int(para.level or 0)
            if not title and level == 0 and len(text) < 120:
                # 无标题占位符时，取第一行短文本当标题
                title = text
                continue
            bullets.append({"level": level, "text": text})
    return title, bullets[:40], tables[:6]


def _is_title_placeholder(shape) -> bool:
    try:
        if not shape.is_placeholder:
            return False
        return int(shape.placeholder_format.idx) == 0
    except Exception:
        return False


def _draw_slide_image(title: str, bullets: list[dict], out_abs: str, out_rel: str,
                      name: str, page_no: int = 0) -> tuple[str, int]:
    """用 Pillow 绘制「版式化预览图」。

    这样即使服务器没装 Office/LibreOffice，学生也能看到图文页面，
    并且体积远小于原 PPT（单页约 30~90KB）。
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        W, H = 1280, 720
        img = Image.new("RGB", (W, H), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        def load_font(size, bold=False):
            candidates = [
                r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\arial.ttf",
            ]
            for p in candidates:
                if os.path.exists(p):
                    try:
                        return ImageFont.truetype(p, size)
                    except Exception:
                        continue
            return ImageFont.load_default()

        # 顶部色带
        draw.rectangle([0, 0, W, 6], fill="#3B82F6")
        y = 56
        if title:
            draw.text((72, y), title[:60], font=load_font(40, True), fill="#0F172A")
            y += 74
        draw.line([72, y - 18, W - 72, y - 18], fill="#E2E8F0", width=2)

        body_font = load_font(26)
        for b in (bullets or [])[:14]:
            lvl = min(int(b.get("level", 0) or 0), 3)
            x = 88 + lvl * 30
            text = b.get("text", "")
            max_w = max(10, (W - x - 80) // 15)
            lines = [text[i:i + max_w] for i in range(0, len(text), max_w)] or [""]
            for li, line in enumerate(lines[:3]):
                if y > H - 90:
                    break
                prefix = ("● " if lvl == 0 else "○ ") if li == 0 else "  "
                draw.text((x, y), prefix + line, font=body_font, fill="#334155")
                y += 38
            y += 6
            if y > H - 90:
                break

        draw.text((72, H - 52), f"{page_no}", font=load_font(18), fill="#94A3B8")

        path = os.path.join(out_abs, name)
        img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        return os.path.join(out_rel, name).replace("\\", "/"), max(1, os.path.getsize(path) // 1024)
    except Exception as e:
        logger.warning(f"slide image draw failed: {e}")
        return "", 0


def _render_slide_only(slide: dict, out_abs: str, out_rel: str, name: str) -> tuple[str, int]:
    """AI 生成的页面（无源文件）直接绘制版式化配图"""
    return _draw_slide_image(slide.get("title", ""), slide.get("bullets") or [],
                             out_abs, out_rel, name, int(slide.get("slide_index", 0)) + 1)


def _slide_to_image(slide, slide_index: int, out_abs: str, out_rel: str,
                    name: str) -> tuple[str, int]:
    """从已加载的 slide 对象生成页面图（不再重复解析整个 PPTX）"""
    title, bullets, _ = _extract_text_shapes(slide)
    return _draw_slide_image(title, bullets, out_abs, out_rel, name, slide_index + 1)


def convert_pptx_to_slides(pptx_path: str, courseware_id: int) -> list[dict[str, Any]]:
    """PPTX → 结构化页面列表（含文本层 + 瘦身图片）

    返回 [{slide_index, title, bullets, notes, tables, image_path, image_kb}]
    """
    from pptx import Presentation
    prs = Presentation(pptx_path)
    out_rel, out_abs = _slides_dir(courseware_id)

    results: list[dict[str, Any]] = []
    for idx, slide in enumerate(prs.slides):
        title, bullets, tables = _extract_text_shapes(slide)

        # 演讲者备注
        notes = ""
        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
                notes = (slide.notes_slide.notes_text_frame.text or "").strip()
        except Exception:
            pass

        # 优先用页面内最大的内嵌图作为该页视觉；没有则版式化渲染兜底
        image_path, image_kb = "", 0
        best_blob, best_size = None, 0
        for shape in slide.shapes:
            if shape.shape_type == 13 and getattr(shape, "image", None) is not None:  # PICTURE
                try:
                    blob = shape.image.blob
                    if len(blob) > best_size:
                        best_blob, best_size = blob, len(blob)
                except Exception:
                    continue
        if best_blob and best_size > MIN_IMAGE_BYTES:
            name = f"s{idx:03d}.jpg"
            image_path, image_kb = _compress_image(best_blob, out_abs, out_rel, name)

        if not image_path:
            name = f"s{idx:03d}.jpg"
            image_path, image_kb = _slide_to_image(slide, idx, out_abs, out_rel, name)

        results.append({
            "slide_index": idx, "title": title, "bullets": bullets,
            "notes": notes[:2000], "tables": tables,
            "image_path": image_path, "image_kb": image_kb,
        })
    return results


def build_ebook_markdown(slides: list[dict[str, Any]], deck_title: str = "") -> str:
    """把散页拼成连贯读物（Markdown），这是「电子书体验」的核心"""
    lines = [f"# {deck_title}" if deck_title else "# 课件读物", ""]
    for s in slides:
        head = s.get("title") or f"第 {s['slide_index'] + 1} 页"
        lines.append(f"## {head}")
        lines.append("")
        bullets = s.get("bullets") or []
        if bullets:
            for b in bullets:
                lvl = min(int(b.get("level", 0) or 0), 3)
                lines.append(f"{'  ' * lvl}- {b.get('text', '')}")
            lines.append("")
        for tbl in (s.get("tables") or [])[:1]:
            if tbl and len(tbl) > 1:
                lines.append("| " + " | ".join(tbl[0]) + " |")
                lines.append("|" + "|".join(["---"] * len(tbl[0])) + "|")
                for row in tbl[1:]:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("")
        if s.get("notes"):
            lines.append(f"> 🗣️ 讲义备注：{s['notes']}")
            lines.append("")
    return "\n".join(lines)


def render_pptx(slides: list[dict[str, Any]], deck_title: str, out_path: str) -> str:
    """结构化页面 → 原生 .pptx（老师上课投影用）"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()

    # 封面
    cover = prs.slides.add_slide(prs.slide_layouts[0])
    cover.shapes.title.text = deck_title or "课件"
    try:
        cover.placeholders[1].text = "由 智研星枢 课程中心生成"
    except Exception:
        pass

    for s in slides:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = s.get("title") or f"第 {s['slide_index'] + 1} 页"
        body = slide.placeholders[1].text_frame
        bullets = s.get("bullets") or []
        first = True
        for b in bullets:
            text = b.get("text", "")
            if not text:
                continue
            para = body.paragraphs[0] if first else body.add_paragraph()
            para.text = text
            para.level = min(int(b.get("level", 0) or 0), 4)
            try:
                para.font.size = Pt(20)
            except Exception:
                pass
            first = False
        if s.get("notes"):
            try:
                slide.notes_slide.notes_text_frame.text = s["notes"]
            except Exception:
                pass
    prs.save(out_path)
    return out_path


def estimate_optimization(original_bytes: int, slides: list[dict[str, Any]]) -> dict:
    """量化转换收益。关键指标是**首屏需下载量**而不是整包体积：
    阅读时只先取文本元数据（几 KB），图片按当前页懒加载，
    因此打开速度由 first_paint_kb 决定，而非整册体积。
    """
    text_kb = sum(len((s.get("title") or "") + "".join(b.get("text", "") for b in (s.get("bullets") or [])))
                  for s in slides) // 1024
    img_kb = sum(s.get("image_kb", 0) or 0 for s in slides)
    total_kb = img_kb + text_kb
    orig_kb = max(1, original_bytes // 1024)
    # 首屏 = 文本元数据 + 首页配图（其余页滑动到才拉）
    first_page_img = (slides[0].get("image_kb", 0) or 0) if slides else 0
    first_paint_kb = max(1, text_kb + first_page_img + len(slides))
    return {
        "original_kb": orig_kb,
        "ebook_kb": total_kb,
        "text_kb": text_kb,
        "image_kb": img_kb,
        "first_paint_kb": first_paint_kb,
        # 打开速度口径：首屏相比原整包下载省了多少
        "saved_percent": max(0, round((1 - first_paint_kb / orig_kb) * 100, 1)),
        # 全量阅读口径（把每页图都加载完的总量）
        "full_load_saved_percent": max(0, round((1 - total_kb / orig_kb) * 100, 1)),
        "lazy_loaded": True,
    }
