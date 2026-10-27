"""课程 AI 服务

对应赛题需求 3、4：
- 需求 3「AI 自动更新陈旧课件」：scan_staleness() 逐页体检（数据/文献/案例是否过时），
  refresh_slides() 只重写被判定陈旧的页面，并保留原版本形成版本链；
- 需求 4「新课程快速做课件」：generate_deck() 依据教学大纲产出结构化幻灯片，
  可直接电子书阅读，也可导出 .pptx 投影使用。
"""
import json
import os
import logging
import re
from typing import Any

from app.agents.qwen_client import call_qwen
from app.agents import model_providers
from app.config import settings
from app.services import mode_policy

logger = logging.getLogger(__name__)

BATCH_SIZE = 8  # 每次体检喂给 LLM 的页数，控制上下文长度

# 通义千问基础模型（向后兼容保留）；真正的可选集由各供应商注册表动态给出，
# 只暴露已配置密钥的供应商，避免把任意字符串或无密钥供应商透传给 API。
SUPPORTED_MODELS = ("qwen-turbo", "qwen-plus", "qwen-max", "qwen-max-longcontext")


def supported_models() -> list[str]:
    """当前可用的全部模型名（仅来自已配置密钥的供应商）"""
    return [m for p in model_providers.configured_providers() for m in p.models]


def resolve_model(model: str | None) -> str:
    """校验前端传入的模型名：命中已配置供应商的模型则用之，否则回退默认（不传死值）"""
    m = (model or "").strip()
    p = model_providers.provider_for_model(m)
    return m if (p and p.configured) else settings.QWEN_MODEL_NAME


class GenerationCancelled(Exception):
    """用户中途停止生成作业（由 should_cancel 探测后抛出，_run_generate_job 捕获落 cancelled 终态）"""


def _extract_json(text: str) -> Any:
    """从 LLM 回复中稳健提取 JSON（支持 ```json 围栏 / 前后缀噪声）"""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    raw = fenced.group(1).strip() if fenced else text.strip()
    try:
        return json.loads(raw)
    except Exception:
        pass
    # 退而求其次：截取第一个 { 或 [
    for opener, closer in (("[", "]"), ("{", "}")):
        s, e = raw.find(opener), raw.rfind(closer)
        if s >= 0 and e > s:
            try:
                return json.loads(raw[s:e + 1])
            except Exception:
                continue
    return None


STALENESS_SYSTEM = """你是资深课程设计助手，擅长判断教学课件内容是否过时。
大学课件常年不更新是普遍问题，你的任务是逐页找出「该更新」的内容。

判定维度：
1. 数据过时 —— 引用了明显陈旧的统计数字、版本、价格、市场规模
2. 文献/理论过时 —— 该领域已有公认的新理论、新发现替代了旧表述
3. 案例陈旧 —— 案例距今久远、企业/技术已消失或被证伪
4. 表述不当 —— 已过时的术语、被推翻的常识、存在争议却写成定论
5. 缺新进展 —— 章节本应覆盖近一两年的重要进展却完全缺失

只对「有实质教学影响」的问题报警，纯风格问题忽略。
严格按 JSON 输出，不要输出多余文字。"""


async def scan_staleness(slides: list[dict], course_title: str = "",
                         domain: str = "", project_id: int = None) -> dict:
    """逐页陈旧度体检

    返回 {"items": [{slide_index, risk_score, category, reason, suggestion}], "cost":..., "summary":...}
    """
    items: list[dict] = []
    total_cost, total_tokens = 0.0, {"input": 0, "output": 0}

    for start in range(0, len(slides), BATCH_SIZE):
        batch = slides[start:start + BATCH_SIZE]
        payload = [{
            "slide_index": s["slide_index"],
            "title": (s.get("title") or "")[:120],
            "bullets": [b.get("text", "")[:200] for b in (s.get("bullets") or [])][:10],
        } for s in batch]

        user_prompt = f"""课程：{course_title or '未命名'}（领域：{domain or '通用'}）
当前参考年份：{__import__('datetime').datetime.now().year}

请体检以下 {len(payload)} 页课件：
{json.dumps(payload, ensure_ascii=False)}

输出 JSON：
{{"items": [{{"slide_index": 页码, "risk_score": 0到1的小数, "category": "数据过时|文献过时|案例陈旧|表述不当|缺新进展|无", "reason": "一句话说明为何需要更新（无问题则留空）", "suggestion": "更新后的该页要点，每行一条，用\\n分隔（无问题则留空）"}}]}}

要求：
- 必须为每一页都给出条目，顺序与输入一致
- risk_score >= 0.4 才视为需要更新
- suggestion 必须是可直接放进课件的正式表述，不要写「建议更新」这种空话"""

        try:
            res = await call_qwen(STALENESS_SYSTEM, user_prompt, project_id=project_id)
            data = _extract_json(res["content"]) or {}
            got = data.get("items") or []
            if isinstance(got, dict):
                got = [got]
            # 容错：模型漏页时按位置补齐
            by_idx = {int(g.get("slide_index", batch[i]["slide_index"])): g for i, g in enumerate(got)}
            for s in batch:
                g = by_idx.get(s["slide_index"], {})
                items.append({
                    "slide_index": s["slide_index"],
                    "risk_score": float(g.get("risk_score", 0) or 0),
                    "category": str(g.get("category", "无") or "无"),
                    "reason": str(g.get("reason", "") or ""),
                    "suggestion": str(g.get("suggestion", "") or ""),
                })
            total_cost += res.get("cost", 0)
            total_tokens["input"] += res["tokens"]["input"]
            total_tokens["output"] += res["tokens"]["output"]
        except Exception as e:
            logger.error(f"staleness batch failed at {start}: {e}")
            for s in batch:
                items.append({"slide_index": s["slide_index"], "risk_score": 0,
                              "category": "扫描失败", "reason": str(e)[:120], "suggestion": ""})

    stale = [i for i in items if i["risk_score"] >= 0.4]
    avg = round(sum(i["risk_score"] for i in items) / max(1, len(items)), 3)
    return {
        "items": items,
        "cost": round(total_cost, 6),
        "tokens": total_tokens,
        "summary": {
            "total_slides": len(items),
            "need_update": len(stale),
            "avg_risk": avg,
            "freshness_score": round(max(0.0, (1 - avg) * 100), 1),  # 0~100，越高越新
            "categories": _count_categories(stale),
        },
    }


def _count_categories(items: list[dict]) -> dict:
    out: dict[str, int] = {}
    for i in items:
        out[i["category"]] = out.get(i["category"], 0) + 1
    return out


REFRESH_SYSTEM = """你是课件内容更新专家。请把陈旧的幻灯片页面改写为当下准确、可直接授课使用的版本。
要求：保留原页的教学目标与结构；更新事实、数据、案例与理论；新增必要的近期进展；
语言为中文书面语；输出严格 JSON。"""


async def refresh_slides(old_slides: list[dict], report_items: list[dict],
                         course_title: str = "", domain: str = "",
                         extra_context: str = "", project_id: int = None) -> tuple[list[dict], dict]:
    """按体检结果重写页面，返回 (新 slides 列表, 用量信息)

    未被判定陈旧的页面原样保留（保持 slide_index 连续）。
    """
    by_idx = {i["slide_index"]: i for i in report_items}
    targets = [s for s in old_slides if by_idx.get(s["slide_index"], {}).get("risk_score", 0) >= 0.4]
    if not targets:
        return [dict(s) for s in old_slides], {"cost": 0, "tokens": {"input": 0, "output": 0}, "updated": 0}

    updated_map: dict[int, dict] = {}
    total_cost, total_tokens = 0.0, {"input": 0, "output": 0}

    for start in range(0, len(targets), 5):
        batch = targets[start:start + 5]
        payload = [{
            "slide_index": s["slide_index"],
            "title": s.get("title", ""),
            "bullets": [b.get("text", "") for b in (s.get("bullets") or [])],
            "diagnosis": {
                "category": by_idx[s["slide_index"]].get("category", ""),
                "reason": by_idx[s["slide_index"]].get("reason", ""),
                "draft": by_idx[s["slide_index"]].get("suggestion", ""),
            },
        } for s in batch]

        user_prompt = f"""课程：{course_title}（{domain}）
当前年份：{__import__('datetime').datetime.now().year}
{('可参考的最新素材：' + extra_context[:3000]) if extra_context else ''}

请更新以下页面：
{json.dumps(payload, ensure_ascii=False)}

输出 JSON：
{{"slides": [{{"slide_index": 页码, "title": "新标题", "bullets": [{{"level": 0, "text": "要点"}}], "notes": "给老师的更新说明：改了哪些事实/为什么改"}}]}}"""

        try:
            res = await call_qwen(REFRESH_SYSTEM, user_prompt, project_id=project_id)
            data = _extract_json(res["content"]) or {}
            for g in (data.get("slides") or []):
                try:
                    idx = int(g.get("slide_index"))
                except Exception:
                    continue
                bullets = g.get("bullets") or []
                norm = []
                for b in bullets:
                    if isinstance(b, dict):
                        norm.append({"level": int(b.get("level", 0) or 0), "text": str(b.get("text", ""))[:400]})
                    else:
                        norm.append({"level": 0, "text": str(b)[:400]})
                updated_map[idx] = {
                    "title": str(g.get("title", ""))[:300],
                    "bullets": norm[:30],
                    "notes": str(g.get("notes", ""))[:2000],
                }
            total_cost += res.get("cost", 0)
            total_tokens["input"] += res["tokens"]["input"]
            total_tokens["output"] += res["tokens"]["output"]
        except Exception as e:
            logger.error(f"refresh batch failed at {start}: {e}")

    new_slides: list[dict] = []
    for s in old_slides:
        base = dict(s)
        upd = updated_map.get(s["slide_index"])
        if upd:
            base.update(upd)
            # 改写过的页文字全新，旧版式语义（卡片/对比/数据/金句）已与新文字对不上，
            # 清掉后退回项目符号版式，避免渲染出过时内容
            for k in ("layout", "kicker", "lead", "cards", "metrics", "compare",
                      "quote", "quote_by", "takeaway", "detail", "example",
                      "chart", "steps", "tables"):
                base.pop(k, None)
            base["updated_by_ai"] = True
            base["risk_score"] = 0.0
            base["risk_category"] = "已更新"
        new_slides.append(base)

    return new_slides, {
        "cost": round(total_cost, 6),
        "tokens": total_tokens,
        "updated": len(updated_map),
    }


def _normalize_slide(s: dict, index: int, chapter: str = "") -> dict:
    """把模型返回的单页规整成落库结构（容错：非 dict bullets / 超长文本截断）

    除了文本层，还保留版式语义（layout/kicker/lead/cards/metrics/compare），
    供 deck_design 渲染成答辩级版面；历史数据没有这些字段也能回退到 bullets。
    """
    bullets = []
    for b in (s.get("bullets") or []):
        if isinstance(b, dict):
            bullets.append({"level": int(b.get("level", 0) or 0), "text": str(b.get("text", ""))[:400]})
        else:
            bullets.append({"level": 0, "text": str(b)[:400]})

    cards = []
    for c in (s.get("cards") or [])[:4]:
        if isinstance(c, dict):
            cards.append({"title": str(c.get("title", ""))[:60],
                          "desc": str(c.get("desc", ""))[:160]})

    metrics = []
    for m in (s.get("metrics") or [])[:3]:
        if isinstance(m, dict):
            metrics.append({"value": str(m.get("value", ""))[:20],
                            "unit": str(m.get("unit", ""))[:10],
                            "label": str(m.get("label", ""))[:60]})

    compare = None
    if isinstance(s.get("compare"), dict):
        c = s["compare"]
        compare = {}
        for side in ("left", "right"):
            d = c.get(side) or {}
            compare[side] = {
                "title": str(d.get("title", ""))[:60],
                "items": [str(x)[:120] for x in (d.get("items") or [])[:4]],
            }

    # 数据图：labels 与 values 必须等长，数字统一转 float（模型常写成 "12%" / "1,200"）
    chart = None
    if isinstance(s.get("chart"), dict):
        c = s["chart"]
        labels = [str(x)[:20] for x in (c.get("labels") or [])[:7]]
        vals = []
        for v in (c.get("values") or [])[:7]:
            try:
                vals.append(float(str(v).replace(",", "").replace("%", "").strip()))
            except (TypeError, ValueError):
                vals.append(0.0)
        n = min(len(labels), len(vals))
        # 负值无法用柱宽/柱高表达，宁可不给 chart（渲染层会退回要点页）
        if n >= 2 and min(vals) >= 0:
            ctype = str(c.get("type") or "bar").strip().lower()
            chart = {
                "type": ctype if ctype in ("bar", "line", "hbar") else "bar",
                "labels": labels[:n], "values": vals[:n],
                "unit": str(c.get("unit") or "")[:8],
                "caption": str(c.get("caption") or "")[:80],
                "series_name": str(c.get("series_name") or c.get("name") or "")[:24],
            }

    # 流程/结构图：2-4 步，标题必须有，否则整页空白
    steps = []
    for st in (s.get("steps") or [])[:4]:
        if isinstance(st, dict) and str(st.get("title") or "").strip():
            steps.append({"title": str(st["title"])[:40],
                          "desc": str(st.get("desc") or "")[:90]})

    return {
        "slide_index": index,
        "chapter": chapter,
        "layout": str(s.get("layout", "") or "")[:20],
        "kicker": str(s.get("kicker", "") or "")[:40],
        "title": str(s.get("title", f"第 {index + 1} 页"))[:300],
        "lead": str(s.get("lead", "") or "")[:200],
        "detail": str(s.get("detail", "") or "")[:400],
        "example": str(s.get("example", "") or "")[:200],
        "chart": chart,
        "steps": steps,
        "key_question": str(s.get("key_question", "") or "")[:200],
        "chapter_no": int(s.get("chapter_no", 0) or 0),
        "bullets": bullets[:20],
        "cards": cards,
        "metrics": metrics,
        "compare": compare,
        "quote": str(s.get("quote", "") or "")[:200],
        "quote_by": str(s.get("quote_by", "") or "")[:80],
        "takeaway": [str(x)[:120] for x in (s.get("takeaway") or [])[:3]],
        "notes": str(s.get("notes", ""))[:2000],
        "tables": s.get("tables") or [],
        "image_path": "",
        "image_kb": 0,
    }


_OUTLINE_SYSTEM = """你是资深课程设计师，擅长把主题拆解成有递进关系的章节大纲。
输出严格 JSON，不要多余文字：
{"title": "建议课件标题", "objectives": ["学习目标1", "学习目标2", "学习目标3"],
 "chapters": [{"title": "章标题", "key_question": "本章要解决的核心问题",
               "points": ["知识点1（具体概念或方法）", "知识点2（含可讲的细节）", "知识点3（含可对比的现象）"]}]}

要求：
- 每章给 3-5 个知识点，知识点要能直接展开成一页，不要写「XX 概述」这类空泛项；
- 章节之间要有递进：先建立直觉，再给方法，再给证据，最后给应用或局限；
- objectives 给 3-5 条，写学生学完能做到什么。"""

_CHAPTER_SYSTEM = """你是顶级课程设计师，也是答辩 PPT 与课堂讲义撰稿人。把指定章节展开成「一页一个论点」的演示页。

硬性要求：
1. 每页只表达一个观点；标题必须是结论句（≤20 字），不要「XX 概述/介绍」这类话题词；
2. lead 用一句话说清本页核心结论（≤45 字），不要重复标题；
3. detail 写「讲透这一页」（80-120 字）：必须给出原理、因果链或操作步骤，能落到数字就落到数字。
   这段是老师上课要讲的原话，不能写成「本页介绍了……」的目录式描述；
4. example 写一个具体案例、例题或应用场景（40-80 字）：必须有具体对象 + 数字或现象 + 结论，
   禁止「例如某系统」这类没有信息量的空话；
5. bullets 版式给 5-6 条主点，每条 22-32 字，必须是「对象 + 动作 + 结果」的完整短句
   （正面例子：「学习率过大时步长激增，损失在最优解附近来回震荡」），
   不要写「定义与作用」这类 4-8 字的名词短语；
   可在主点下补 1-2 条 level=1 的子点（≤38 字），写「为什么」「怎么做」「常见误区」；
6. 从下列版式中选一种，只填该版式需要的字段：
   - bullets：主点 + 子点（最常用，默认）
   - cards：2-4 个并列要素，title ≤12 字、desc ≤40 字（要写出各自的作用，不是标签）
   - compare：两组对照，各 2-3 条，每条 ≤22 字
   - metric：2-3 个关键数字，value 为数字、unit 为单位、label ≤20 字
   - chart：一页数据图，chart={"type":"bar|line|hbar","unit":"%","labels":[2-6 个类别],"values":[同长度的真实数字],"caption":"数据来源","series_name":"指标名"}
     （values 只写数字不带单位；一页只能同一量纲，百分比与耗时/分数不能混画）
   - flow：2-4 步流程/机制，steps=[{"title":"步骤名≤12 字","desc":"≤45 字，说清这一步输入什么、做什么、输出什么"}]
   - table：对照表，表头 2-4 列，2-4 行数据，单元格写具体内容而不是「是/否」
           tables=[[["表头1","表头2"],["第1行1","第1行2"],["第2行1","第2行2"]]]
   - quote：一句可被记住的结论（≤45 字）
7. 同一章内版式不得重复，且本章必须至少有 1 页 chart 或 flow（要有图），至少 1 页 table 或 compare（要有对照）；
   本章最后一页固定写「本章小结」：layout=bullets，标题「本章小结：<一句结论>」，
   bullets 用 3-4 条回顾主线，takeaway 给 3 条可带走的结论；
8. 事实与数据必须准确；没把握就写「已有研究表明」；优先融入近 1-2 年的真实进展；
9. kicker 写所属小节名（≤8 字），让页面有导航感；
10. notes 写给讲师的授课速记（120-200 字）：怎么开场、这一页讲几分钟、
    举什么例、学生易问什么、哪一句要放慢语速强调，五件事都要写到；
11. 直接进入内容，不要写「本章导览」这种空页（章节过渡页由系统生成）；
12. 输出前逐页自检：主点是否 5-6 条且每条 ≥22 字、detail 是否 ≥80 字、
    notes 是否 ≥120 字；任一项不达标就补写，宁可信息密一点，也不要交空页；
13. 输出严格 JSON，不要多余文字：
{"slides": [{"layout": "bullets", "kicker": "小节名", "title": "结论式标题", "lead": "一句话结论",
  "detail": "讲透这一页的解释", "example": "具体案例",
  "bullets": [{"level": 0, "text": "主点"}, {"level": 1, "text": "补充说明"}],
  "cards": [], "metrics": [], "chart": null, "steps": [], "tables": [],
  "compare": {"left": {"title": "", "items": []}, "right": {"title": "", "items": []}},
  "takeaway": [], "notes": "讲师速记"}]}"""


async def generate_deck(topic: str, syllabus: str = "", chapter_count: int = 6,
                        slides_per_chapter: int = 5, style: str = "标准",
                        audience: str = "本科生", domain: str = "",
                        reference_material: str = "", project_id: int = None,
                        on_progress=None, model: str = None, mode: str = None,
                        should_cancel=None) -> tuple[list[dict], dict]:
    """新课程快速做课件：先出大纲，再逐章生成，全程上报进度

    on_progress(stage, percent, message, extra) 由调用方传入（课件工坊的作业循环），
    让前端进度条显示“第几章/共几页”这种真实进展，而不是一个转圈的盲等。
    分章生成还顺带解决了旧版一次性输出 80 页时被 max_tokens 截断的问题。
    model：命白名单则用该模型，否则用默认；should_cancel() 为真时抛 GenerationCancelled。
    mode：'quick'/'expert' —— 决定模型档位（用户未显式选模型时）、内容深度指令与逐页篇幅；
    两档都保留版式硬约束（每章≥1图+≥1对照），保证都图文并茂。
    """
    policy = mode_policy.apply_mode(mode, model, long_text=reference_material)
    mdl = resolve_model(policy["model"])
    cw = policy["courseware"]
    directive = policy["directive"]
    # 实际用到的模型（限流时 qwen_client 会自动回退，这里如实记录供前端提示）
    models_used: list[str] = []

    def _track(res: dict) -> None:
        m = str(res.get("model") or mdl)
        if m not in models_used:
            models_used.append(m)

    def _cancelled() -> bool:
        return bool(should_cancel and should_cancel())

    async def _emit(stage: str, percent: int, message: str, **extra):
        if on_progress:
            try:
                await on_progress(stage, int(percent), message, extra)
            except Exception as e:  # 进度上报绝不能拖垮生成主流程
                logger.debug(f"progress emit skipped: {e}")

    chapter_count = max(1, min(int(chapter_count or 6), 12))
    slides_per_chapter = max(1, min(int(slides_per_chapter or 5), 8))
    # 每章额外一页章节过渡页（section），末尾多小结页与结课页
    cap = min(chapter_count * (slides_per_chapter + 1) + 3, 80)
    cost, tin, tout = 0.0, 0, 0
    syl_block = ("\n教学大纲：\n" + syllabus[:3000]) if syllabus else ""
    ref_block = ("\n参考资料（优先吸收其中的事实与数据）：\n" + reference_material[:5000]) if reference_material else ""

    # ── 1. 大纲 ──
    if _cancelled():
        raise GenerationCancelled()
    await _emit("outline", 6, "正在设计章节大纲…")
    res = await call_qwen(_OUTLINE_SYSTEM + "\n" + directive, f"""主题：{topic}
领域：{domain or '通用'}
授课对象：{audience}
风格：{style}
章节数：{chapter_count}，每章约 {slides_per_chapter} 页{syl_block}{ref_block}

只输出 JSON。""", project_id=project_id, max_tokens=cw["outline_tokens"], model=mdl)
    _track(res)
    cost += res.get("cost", 0)
    tin += res["tokens"]["input"]
    tout += res["tokens"]["output"]
    data = _extract_json(res["content"]) or {}
    chapters = [c for c in (data.get("chapters") or []) if isinstance(c, dict)][:chapter_count]
    if not chapters:
        chapters = [{"title": f"第 {i + 1} 部分", "points": []} for i in range(chapter_count)]
    objectives = [str(o)[:200] for o in (data.get("objectives") or [])][:5]

    deck_title = str(data.get("title") or topic)[:300]
    slides: list[dict] = [_normalize_slide({
        "layout": "cover",
        "chapter": "封面",
        "kicker": f"{style} · 面向{audience}"[:40],
        "title": deck_title,
        "lead": f"{topic}｜共 {chapter_count} 章 · 约 {chapter_count * slides_per_chapter} 页",
        # 学习目标保留在文本层（讲义/大纲会用到）；封面版式不画 bullets
        "bullets": [{"level": 0, "text": o} for o in objectives][:4],
        "notes": f"开场：一句话说明课程定位（{topic}），再点出本课要解决的 2-3 个问题。",
    }, 0, "封面")]

    # ── 2. 逐章生成 ──
    base, span = 10, 78
    for i, ch in enumerate(chapters):
        if _cancelled():
            raise GenerationCancelled()
        chapter_name = str(ch.get("title", f"第 {i + 1} 部分"))[:200]
        await _emit("chapter", base + int(span * i / len(chapters)),
                    f"正在生成第 {i + 1}/{len(chapters)} 章：{chapter_name[:24]}",
                    chapters_done=i, chapters_total=len(chapters),
                    slides_done=len(slides), slides_total=cap)
        key_q = str(ch.get("key_question", "") or "")[:120]
        # 章节过渡页：大编号 + 本章关键问题，让整套课件有答辩式的章节感
        if len(slides) < cap:
            slides.append(_normalize_slide({
                "layout": "section", "chapter": chapter_name, "chapter_no": i + 1,
                "title": chapter_name, "key_question": key_q,
                "notes": f"过渡：先抛出「{key_q or chapter_name}」，停一拍再进入正文。",
            }, len(slides), chapter_name))
        pts = [str(p)[:80] for p in (ch.get("points") or [])]
        pts_text = "；".join(pts) or "自拟"
        # 每页要带 detail / example / notes，输出量比旧版翻倍，token 上限同步放大
        cres = await call_qwen(_CHAPTER_SYSTEM, f"""课程主题：{topic}（{domain or '通用'} · 面向 {audience} · {style}）
本章标题：{chapter_name}
本章要解决的问题：{key_q or '自拟'}
本章知识点：{pts_text}
{directive}
请输出 {slides_per_chapter} 页：同一章内版式不重复，其中至少 1 页用 chart 画数据、
至少 1 页用 flow 画流程或 table 做对照，最后一页固定是本章小结，
其余页面用 bullets（4-6 条主点 + 子点，带 detail 与 example）。
每页都要有 detail（{cw['detail']} 字）、example（40-80 字）与 notes（150-250 字）。{ref_block if i == 0 else ''}

只输出 {{"slides": [...]}}。""", project_id=project_id,
                              max_tokens=min(8000, cw["chapter_base_tokens"] + slides_per_chapter * 1200), model=mdl)
        _track(cres)
        cost += cres.get("cost", 0)
        tin += cres["tokens"]["input"]
        tout += cres["tokens"]["output"]
        got = _extract_json(cres["content"]) or {}
        rows = got.get("slides") or []
        if isinstance(rows, dict):
            rows = [rows]
        for s in rows[:slides_per_chapter]:
            if len(slides) >= cap:
                break
            if isinstance(s, dict):
                slides.append(_normalize_slide(s, len(slides), chapter_name))
        await _emit("chapter", base + int(span * (i + 1) / len(chapters)),
                    f"第 {i + 1}/{len(chapters)} 章完成（累计 {len(slides)} 页）",
                    chapters_done=i + 1, chapters_total=len(chapters),
                    slides_done=len(slides), slides_total=cap)

    # ── 3. 小结页 + 思考题 + 延伸阅读（讲义要用后两项）──
    if _cancelled():
        raise GenerationCancelled()
    await _emit("summary", 92, "正在生成小结、思考题与延伸阅读…")
    def _line(j: int, c: dict) -> str:
        pts = "、".join(str(p)[:40] for p in (c.get("points") or [])[:4])
        return f"{j + 1}. {c.get('title', '')}：{pts}"

    outline_txt = "\n".join(_line(j, c) for j, c in enumerate(chapters))
    exercises: list[str] = []
    reading: list[str] = []
    final_takeaway: list[str] = []
    try:
        sres = await call_qwen(
            "你是课程总结助手。输出严格 JSON："
            '{"wrap": {"layout": "bullets", "kicker": "全课回顾", "title": "本页标题", '
            '"lead": "一句话总结本课主线", "detail": "串起全课因果链的回顾", '
            '"bullets": [{"level": 0, "text": "完整短句"}], '
            '"takeaway": ["关键词1", "关键词2", "关键词3"], "notes": "讲师速记"}, '
            '"exercises": ["思考题"], "reading": ["延伸阅读"]}',
            f"课程主题：{topic}（面向 {audience}）\n章节与知识点：\n{outline_txt}\n\n"
            f"请给出：结课小结页（4 条回顾主线的完整短句，每条 22-32 字，"
            f"另给 detail 80-120 字串起全课因果链、notes 150 字以上的结课速记）、"
            f"3 个可带走的结论（takeaway，每条≤22 字）、3 道思考题、2-4 条延伸阅读建议。\n只输出 JSON。",
            project_id=project_id, max_tokens=2000, model=mdl)
        _track(sres)
        cost += sres.get("cost", 0)
        tin += sres["tokens"]["input"]
        tout += sres["tokens"]["output"]
        sdata = _extract_json(sres["content"]) or {}
        wrap = sdata.get("wrap") or {}
        if isinstance(wrap, dict) and (wrap.get("bullets") or wrap.get("takeaway")):
            wrap.setdefault("layout", "bullets")
            wrap.setdefault("kicker", "全课回顾")
            slides.append(_normalize_slide(wrap, len(slides), "小结"))
            final_takeaway = [str(x)[:120] for x in (wrap.get("takeaway") or [])][:3]
        exercises = [str(x)[:300] for x in (sdata.get("exercises") or [])][:8]
        reading = [str(x)[:300] for x in (sdata.get("reading") or [])][:8]
    except Exception as e:
        logger.warning(f"小结页生成跳过（不影响课件主体）: {e}")

    # ── 4. 结课页：把小结收敛成 3 个可带走的结论 ──
    if not final_takeaway:
        final_takeaway = [b.get("text", "") for b in (slides[-1].get("bullets") or [])
                          if b.get("text")][:3]
    slides.append(_normalize_slide({
        "layout": "end", "chapter": "结课", "title": "谢谢",
        "takeaway": final_takeaway or [f"回顾：{topic}", "方法：把结论讲成一句话", "下一步：完成思考题"],
        "notes": "结课：回收三个关键词，留 2 分钟提问。",
    }, len(slides), "结课"))

    # ── 5. 统一重排页码（插入过渡页后索引必须连续）──
    for idx, s in enumerate(slides):
        s["slide_index"] = idx

    if len(slides) < 2:
        return [], {"chapters": chapters, "cost": round(cost, 6)}

    await _emit("assemble", 96, f"已组装 {len(slides)} 页，准备落库…",
                slides_done=len(slides), slides_total=len(slides))
    return slides, {
        "chapters": chapters,
        "objectives": objectives,
        "exercises": exercises,
        "reading": reading,
        "model": mdl,
        "mode": policy["mode"],
        "models_used": models_used or [mdl],
        "cost": round(cost, 6),
        "tokens": {"input": tin, "output": tout},
    }


async def outline_from_syllabus(text: str, domain: str = "", project_id: int = None,
                                mode: str = None) -> dict:
    """辅助联动：把粘贴的大纲/研报文本抽取成章节结构

    mode：'quick' 每章只提 3-4 个核心知识点；'expert' 每章展开更细（5-8 个知识点、可再带子项）。
    """
    policy = mode_policy.apply_mode(mode, long_text=text)
    fine = ("每章提炼 5-8 个知识点，尽量把原理、方法、案例都覆盖到。"
            if policy["mode"] == mode_policy.EXPERT
            else "每章只留 3-4 个最核心的知识点，抓主干。")
    user_prompt = f"""把下面的课程材料整理为章节大纲。领域：{domain or '通用'}
{fine}
材料：
{text[:6000]}

输出 JSON：{{"title": "建议课程名", "domain": "领域", "chapters": [{{"title": "章名", "points": ["知识点"]}}]}}"""
    res = await call_qwen("你是课程设计助手，输出严格 JSON。", user_prompt,
                          project_id=project_id, max_tokens=policy["courseware"]["outline_tokens"],
                          model=policy["model"])
    return (_extract_json(res["content"]) or {}), {"cost": res.get("cost", 0)}


# ═══════════════════════════════════════════════════════
#  多源素材聚合：让课件能用上「原资料 / 科学问题 / 对话 / 技能 / 流水线」
# ═══════════════════════════════════════════════════════

async def collect_material(db, user, sources: dict, topic: str = "",
                           per_source_limit: int = 6000) -> tuple[str, list[dict]]:
    """从系统各模块拉取素材，返回 (拼接后的参考文本, 来源清单)。

    sources 支持键：
      doc_ids         资料库文档（上传的原资料）
      question_ids    Science 125 科学问题（题目作为教学靶点）
      task_ids        题目生成任务（已产出的完整研究报告）
      project_id      研究项目（问题 + 假设 + 领域）
      chat_project_id 从项目对话历史里取师生问答
      pipeline_run_id 流水线运行结果（各 Agent 步骤摘要）
      skill_runs      [{skill_id, input_data}] 调用技能市场（含 git/webhook 外接技能）
    """
    import json as _json
    from sqlalchemy import select
    from app.database.models import Document, ScienceQuestion, QuestionTask, Project, ChatMessage

    blocks: list[str] = []
    provenance: list[dict] = []

    def add(label: str, text: str, kind: str, ref: str):
        text = (text or "").strip()
        if not text:
            return
        blocks.append(f"===== 【{label}】 =====\n{text[:per_source_limit]}")
        provenance.append({"kind": kind, "ref": ref, "label": label, "chars": len(text)})

    # 1) 资料库原资料
    for did in (sources.get("doc_ids") or [])[:5]:
        try:
            doc = (await db.execute(select(Document).where(Document.id == int(did)))).scalar_one_or_none()
            if not doc:
                continue
            content = (doc.structured_data or {}).get("content") or doc.summary or ""
            add(f"资料库《{doc.filename}》", content, "document", str(doc.id))
        except Exception as e:
            logger.warning(f"material doc {did} failed: {e}")

    # 2) 科学问题题库
    for qid in (sources.get("question_ids") or [])[:8]:
        try:
            q = (await db.execute(select(ScienceQuestion).where(
                ScienceQuestion.question_id == int(qid)))).scalar_one_or_none()
            if not q:
                continue
            txt = (f"{q.title}\n{q.description or ''}\n关键词：{', '.join(q.keywords or [])}"
                   f"\n难度：{q.difficulty}")
            add(f"科学问题 #{q.question_id}", txt, "question", str(q.question_id))
        except Exception as e:
            logger.warning(f"material question {qid} failed: {e}")

    # 3) 题目研究报告
    for tid in (sources.get("task_ids") or [])[:3]:
        try:
            task = (await db.execute(select(QuestionTask).where(QuestionTask.id == int(tid))
                                     )).scalar_one_or_none()
            if not task:
                continue
            result = task.result or {}
            text = result.get("document") or result.get("report") or result.get("full_text") or ""
            if not text:
                text = "\n\n".join(
                    f"【{k}】\n" + (v if isinstance(v, str) else
                                    _json.dumps(v, ensure_ascii=False)[:1500])
                    for k, v in list(result.items())[:8] if v)
            if not text and task.document_path and os.path.exists(task.document_path):
                try:
                    with open(task.document_path, encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                except Exception:
                    pass
            add(f"研究报告（任务 #{task.id}）", text, "question_task", str(task.id))
        except Exception as e:
            logger.warning(f"material task {tid} failed: {e}")

    # 4) 研究项目
    if sources.get("project_id"):
        try:
            proj = (await db.execute(select(Project).where(
                Project.id == int(sources["project_id"])))).scalar_one_or_none()
            if proj:
                txt = (f"{proj.title}\n研究问题：{proj.research_question or ''}\n"
                       f"假设：{getattr(proj, 'hypothesis', '') or ''}\n领域：{proj.domain or ''}")
                add(f"研究项目《{proj.title}》", txt, "project", str(proj.id))
        except Exception as e:
            logger.warning(f"material project failed: {e}")

    # 5) 对话历史
    if sources.get("chat_project_id"):
        try:
            msgs = (await db.execute(select(ChatMessage).where(
                ChatMessage.project_id == int(sources["chat_project_id"]))
                .order_by(ChatMessage.created_at.desc()).limit(20))).scalars().all()
            txt = "\n".join(f"{m.role}: {m.content[:300]}" for m in reversed(list(msgs)))
            add("课程相关对话问答", txt, "chat", str(sources["chat_project_id"]))
        except Exception as e:
            logger.warning(f"material chat failed: {e}")

    # 6) 研究流水线运行结果
    if sources.get("pipeline_run_id"):
        try:
            from app.database.models import PipelineRun
            run = (await db.execute(select(PipelineRun).where(
                PipelineRun.id == str(sources["pipeline_run_id"])))).scalar_one_or_none()
            if run:
                parts = []
                for st in (run.steps_log or []):
                    summ = st.get("result_summary") or st.get("output") or ""
                    if summ:
                        step_name = st.get("step") or st.get("agent_name") or "step"
                        parts.append(f"【{step_name}】\n{str(summ)[:1800]}")
                add(f"研究流水线产出（run {str(run.id)[:8]}）", "\n\n".join(parts),
                    "pipeline_run", str(run.id))
        except Exception as e:
            logger.warning(f"material pipeline run failed: {e}")

    # 7) 技能市场（内置 / 自定义 / git 或网上导入的 webhook 技能）
    for spec in (sources.get("skill_runs") or [])[:3]:
        sid = spec.get("skill_id") if isinstance(spec, dict) else spec
        if not sid:
            continue
        try:
            from app.api.v1.skills import run_skill, SkillRunRequest
            input_data = dict(spec.get("input_data") or {}) if isinstance(spec, dict) else {}
            input_data.setdefault("question", topic)
            input_data.setdefault("topic", topic)
            out = await run_skill(SkillRunRequest(skill_id=sid, input_data=input_data,
                                                 project_id=sources.get("project_id")), user, db)
            body = out.get("result") if isinstance(out, dict) else out
            if isinstance(body, dict):
                body = (body.get("content") or body.get("result") or body.get("answer")
                        or _json.dumps(body, ensure_ascii=False)[:per_source_limit])
            name = out.get("skill_name", sid) if isinstance(out, dict) else sid
            add(f"技能产出（{name}）", str(body or ""), "skill", str(sid))
        except Exception as e:
            logger.warning(f"material skill {sid} failed: {e}")

    return ("\n\n".join(blocks) if blocks else ""), provenance
