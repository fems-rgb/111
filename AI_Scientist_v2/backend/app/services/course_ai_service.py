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

logger = logging.getLogger(__name__)

BATCH_SIZE = 8  # 每次体检喂给 LLM 的页数，控制上下文长度


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
            base["updated_by_ai"] = True
            base["risk_score"] = 0.0
            base["risk_category"] = "已更新"
        new_slides.append(base)

    return new_slides, {
        "cost": round(total_cost, 6),
        "tokens": total_tokens,
        "updated": len(updated_map),
    }


GENERATE_SYSTEM = """你是高校课程设计专家。根据教学大纲生成一套可直接授课使用的课件（幻灯片）。
原则：
1. 每页只讲一件事，标题是结论式表述而非话题词
2. 要点 3-6 条，具体可讲，避免「介绍一下」「概述」这类空话
3. 融入近 1-2 年的真实进展、数据与案例
4. notes 写讲师速记（案例出处、可能的学生提问、板书提示）
5. 输出严格 JSON，不要多余文字"""


async def generate_deck(topic: str, syllabus: str = "", chapter_count: int = 6,
                        slides_per_chapter: int = 4, style: str = "标准",
                        audience: str = "本科生", domain: str = "",
                        reference_material: str = "", project_id: int = None) -> tuple[list[dict], dict]:
    """新课程快速做课件：生成结构化幻灯片列表"""
    total = min(chapter_count * slides_per_chapter, 80)
    user_prompt = f"""请为下面的课程设计一套课件。

主题：{topic}
领域：{domain or '通用'}
授课对象：{audience}
风格：{style}
章节数：{chapter_count}，每约 {slides_per_chapter} 页，共约 {total} 页
{('教学大纲：\n' + syllabus[:4000]) if syllabus else ''}
{('参考资料（请优先吸收其中的事实与数据）：\n' + reference_material[:6000]) if reference_material else ''}

输出 JSON：
{{"chapters": [{{"title": "章标题", "points": ["知识点1", "知识点2"]}}],
 "slides": [{{"slide_index": 0, "chapter": "所属章", "title": "页标题",
   "bullets": [{{"level": 0, "text": "要点"}}], "notes": "讲师速记"}}]}}

要求：第 0 页为封面页（title=课程名，bullets 写课程定位与学习目标）；最后一页为小结与延伸阅读。"""

    res = await call_qwen(GENERATE_SYSTEM, user_prompt, project_id=project_id,
                          max_tokens=min(8192, 2048 + total * 90))
    data = _extract_json(res["content"]) or {}
    raw_slides = data.get("slides") or []
    slides: list[dict] = []
    for i, s in enumerate(raw_slides[:total]):
        bullets = []
        for b in (s.get("bullets") or []):
            if isinstance(b, dict):
                bullets.append({"level": int(b.get("level", 0) or 0), "text": str(b.get("text", ""))[:400]})
            else:
                bullets.append({"level": 0, "text": str(b)[:400]})
        slides.append({
            "slide_index": i,
            "title": str(s.get("title", f"第 {i + 1} 页"))[:300],
            "bullets": bullets[:20],
            "notes": str(s.get("notes", ""))[:2000],
            "tables": [],
            "image_path": "",
            "image_kb": 0,
        })
    return slides, {
        "chapters": data.get("chapters") or [],
        "cost": round(res.get("cost", 0), 6),
        "tokens": res.get("tokens", {"input": 0, "output": 0}),
        "model": res.get("model", ""),
    }


async def outline_from_syllabus(text: str, domain: str = "", project_id: int = None) -> dict:
    """辅助联动：把粘贴的大纲/研报文本抽取成章节结构"""
    user_prompt = f"""把下面的课程材料整理为章节大纲。领域：{domain or '通用'}

材料：
{text[:6000]}

输出 JSON：{{"title": "建议课程名", "domain": "领域", "chapters": [{{"title": "章名", "points": ["知识点"]}}]}}"""
    res = await call_qwen("你是课程设计助手，输出严格 JSON。", user_prompt, project_id=project_id)
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
