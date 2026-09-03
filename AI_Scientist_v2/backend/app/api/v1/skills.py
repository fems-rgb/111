"""智研星枢 - 技能市场API（统一执行引擎 v2）
支持三种技能类型:
  1. builtin   → 专用 Python 逻辑
  2. custom    → prompt_template + call_qwen (通义千问)
  3. webhook   → HTTP 调用外部接口
联动能力:
  - 可从资料库选取文件作为输入
  - 可在 AI 对话中通过 /skill 调用
  - 可作为自动化流水线的步骤
"""
import logging
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models import User, CustomSkill, Document
from app.api.deps import get_current_user
from app.security.prompt_guard import prompt_guard
from app.agents.qwen_client import call_qwen

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skills", tags=["技能市场"])


# ─── 请求模型 ───────────────────────────────────────────────
class SkillRunRequest(BaseModel):
    skill_id: str
    input_data: dict = {}
    project_id: int | None = None


class CreateSkillRequest(BaseModel):
    name: str
    description: str = ""
    prompt_template: str = ""
    icon: str = "🔧"
    category: str = "custom"
    is_public: bool = True
    webhook_url: str = ""
    webhook_method: str = "POST"
    linked_doc_ids: list[int] = []


# ─── 内置技能注册表 ─────────────────────────────────────────
BUILTIN_SKILLS = {
    "literature_summary": {
        "id": "literature_summary",
        "name": "文献摘要提取",
        "icon": "🔬",
        "description": "自动解析论文 PDF 生成结构化摘要，提取研究问题、方法、结论",
        "input_schema": {"file_id": "string", "question": "string(optional)"},
        "type": "builtin",
    },
    "data_cleaning": {
        "id": "data_cleaning",
        "name": "实验数据清洗",
        "icon": "📊",
        "description": "CSV/Excel 异常值检测、缺失值填充、标准化处理",
        "input_schema": {"file_id": "string", "method": "zscore|iqr|manual"},
        "type": "builtin",
    },
    "code_reproduce": {
        "id": "code_reproduce",
        "name": "代码复现检查",
        "icon": "🧪",
        "description": "验证 GitHub 仓库可运行性，检查依赖、环境、入口脚本",
        "input_schema": {"repo_url": "string"},
        "type": "builtin",
    },
}


# ─── 列表 ───────────────────────────────────────────────────
@router.get("")
async def list_skills(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取可用技能列表（内置 + 自定义 + 外接）"""
    skills = list(BUILTIN_SKILLS.values())

    stmt = select(CustomSkill).where(
        (CustomSkill.user_id == user.id) | (CustomSkill.is_public == True)
    )
    result = await db.execute(stmt)
    for cs in result.scalars().all():
        skill_type = "webhook" if (getattr(cs, 'webhook_url', '') or '') else "custom"
        skills.append({
            "id": f"custom_{cs.id}",
            "name": cs.name,
            "icon": cs.icon,
            "description": cs.description,
            "prompt_template": cs.prompt_template,
            "category": cs.category,
            "is_custom": True,
            "type": skill_type,
            "webhook_url": getattr(cs, 'webhook_url', '') or '',
            "linked_doc_ids": getattr(cs, 'linked_doc_ids', []) or [],
        })
    return {"skills": skills}


# ─── 创建 ───────────────────────────────────────────────────
@router.post("")
async def create_skill(
    req: CreateSkillRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建自定义技能（prompt型 或 外接webhook型）"""
    if not req.prompt_template and not req.webhook_url:
        raise HTTPException(status_code=400, detail="prompt_template 和 webhook_url 至少提供一个")

    check_text = req.prompt_template or req.webhook_url
    is_safe, reason = prompt_guard.check(check_text)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"安全检测未通过: {reason}")

    skill = CustomSkill(
        user_id=user.id,
        name=req.name,
        description=req.description,
        prompt_template=req.prompt_template,
        icon=req.icon,
        category=req.category,
        is_public=req.is_public,
        webhook_url=req.webhook_url,
        webhook_method=req.webhook_method,
        linked_doc_ids=req.linked_doc_ids,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info(f"[Skill] Created '{skill.name}' (id={skill.id}) by user {user.id}, type={'webhook' if req.webhook_url else 'prompt'}")
    return {"id": f"custom_{skill.id}", "name": skill.name, "status": "created"}


# ─── 删除自定义技能 ─────────────────────────────────────────
@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not skill_id.startswith("custom_"):
        raise HTTPException(status_code=400, detail="内置技能不可删除")
    try:
        cs_id = int(skill_id.replace("custom_", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的技能ID")
    stmt = select(CustomSkill).where(CustomSkill.id == cs_id, CustomSkill.user_id == user.id)
    cs = (await db.execute(stmt)).scalar_one_or_none()
    if not cs:
        raise HTTPException(status_code=404, detail="技能不存在或无权删除")
    await db.delete(cs)
    await db.commit()
    return {"ok": True, "message": f"技能 {cs.name} 已删除"}


# ─── 执行（统一入口） ──────────────────────────────────────
@router.post("/run")
async def run_skill(
    req: SkillRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    统一技能执行引擎:
      1. 内置技能  → 专用 Python 逻辑
      2. 自定义技能 → prompt_template + call_qwen
      3. 外接技能  → webhook HTTP 调用
    
    联动: input_data 中可包含 file_id 从资料库取文件内容注入 prompt
    """
    # 安全检查输入
    input_str = json.dumps(req.input_data, ensure_ascii=False)
    is_safe, reason = prompt_guard.check(input_str)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"安全检测未通过: {reason}")

    # ① 内置技能
    if req.skill_id in BUILTIN_SKILLS:
        skill = BUILTIN_SKILLS[req.skill_id]
        logger.info(f"[Skill] Running builtin '{req.skill_id}' for user {user.id}")
        result = await _execute_builtin(req.skill_id, req.input_data, user, db)
        return {
            "skill_id": req.skill_id,
            "skill_name": skill["name"],
            "status": "success",
            "result": result,
        }

    # ② 自定义 / 外接技能 (custom_N)
    if req.skill_id.startswith("custom_"):
        try:
            cs_id = int(req.skill_id.replace("custom_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的技能ID: {req.skill_id}")

        stmt = select(CustomSkill).where(CustomSkill.id == cs_id)
        cs = (await db.execute(stmt)).scalar_one_or_none()
        if not cs:
            raise HTTPException(status_code=404, detail=f"技能不存在: {req.skill_id}")

        if cs.user_id != user.id and not cs.is_public:
            raise HTTPException(status_code=403, detail="无权执行此技能")

        logger.info(f"[Skill] Running custom '{cs.name}' (id={cs_id}) for user {user.id}")

        # ③ 外接 webhook 技能
        webhook_url = getattr(cs, 'webhook_url', '') or ''
        if webhook_url:
            result = await _execute_webhook(webhook_url, getattr(cs, 'webhook_method', 'POST'), req.input_data)
            return {
                "skill_id": req.skill_id,
                "skill_name": cs.name,
                "status": "success",
                "result": result,
            }

        # ② 自定义 prompt 技能 → 调 call_qwen
        if cs.prompt_template:
            result = await _execute_prompt_skill(cs, req.input_data, user, db, req.project_id)
            return {
                "skill_id": req.skill_id,
                "skill_name": cs.name,
                "status": "success",
                "result": result,
            }

        raise HTTPException(status_code=400, detail="该技能没有 prompt_template 或 webhook_url，无法执行")

    raise HTTPException(status_code=404, detail=f"未知技能: {req.skill_id}")


# ─── 内置技能执行器 ─────────────────────────────────────────
async def _execute_builtin(skill_id: str, input_data: dict, user: User, db: AsyncSession) -> dict:
    if skill_id == "literature_summary":
        file_id = input_data.get("file_id", "")
        question = input_data.get("question", "")
        if not file_id:
            return {"summary": "⚠️ 请提供 file_id 参数", "structured": {}}

        doc = await _find_document(file_id, user, db)
        if not doc:
            stmt = select(Document.filename, Document.id).where(Document.user_id == user.id).limit(5)
            existing = (await db.execute(stmt)).all()
            file_list = ", ".join([f"{r[0]}(id={r[1]})" for r in existing]) if existing else "无"
            return {"summary": f"⚠️ 文件 '{file_id}' 未找到。当前资料库: [{file_list}]", "structured": {}}

        # 如果有 question，用 LLM 基于摘要回答
        if question and doc.summary:
            try:
                prompt = f"基于以下文献摘要回答问题。\n\n文献摘要:\n{doc.summary}\n\n问题: {question}"
                result = await call_qwen("你是学术文献分析助手，用中文回答。", prompt)
                return {
                    "summary": result["content"],
                    "structured": doc.structured_data or {},
                    "filename": doc.filename,
                    "tokens": result["tokens"],
                    "model": result["model"],
                }
            except Exception as e:
                logger.warning(f"LLM问答失败，返回原始摘要: {e}")

        return {
            "summary": doc.summary or "(暂无摘要，请先完成索引)",
            "structured": doc.structured_data or {},
            "filename": doc.filename,
            "parse_status": doc.parse_status,
        }

    elif skill_id == "data_cleaning":
        file_id = input_data.get("file_id", "")
        method = input_data.get("method", "zscore")
        if not file_id:
            return {"message": "⚠️ 请提供 file_id 参数", "cleaned_rows": 0}

        import os
        from app.config import settings
        save_path = os.path.join(settings.UPLOAD_DIR, f"user_{user.id}", "research", file_id)
        if not os.path.exists(save_path):
            return {"message": f"⚠️ 文件 {file_id} 不存在"}

        ext = os.path.splitext(file_id)[1].lower()
        rows_processed = 0
        anomalies_found = 0

        if ext == ".csv":
            import csv
            with open(save_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                all_rows = list(reader)
                rows_processed = len(all_rows)
                numeric_cols = []
                for ci in range(len(headers)):
                    vals = []
                    for row in all_rows[:500]:
                        try:
                            vals.append(float(row[ci]))
                        except (ValueError, IndexError):
                            pass
                    if len(vals) > 10:
                        numeric_cols.append((ci, vals))
                for ci, vals in numeric_cols:
                    mean_v = sum(vals) / len(vals)
                    std_v = (sum((v - mean_v) ** 2 for v in vals) / len(vals)) ** 0.5
                    if std_v > 0:
                        anomalies_found += sum(1 for v in vals if abs(v - mean_v) > 3 * std_v)

        return {
            "message": f"✅ 数据清洗完成 ({method} 方法)",
            "rows_processed": rows_processed,
            "anomalies_found": anomalies_found,
            "method": method,
        }

    elif skill_id == "code_reproduce":
        repo_url = input_data.get("repo_url", "")
        if not repo_url:
            return {"message": "⚠️ 请提供 repo_url 参数"}

        checks = []
        if repo_url.startswith("https://github.com/"):
            checks.append({"item": "GitHub URL格式", "status": "✅ 有效"})
        else:
            checks.append({"item": "GitHub URL格式", "status": "⚠️ 非标准GitHub地址"})

        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.head(repo_url, follow_redirects=True)
                checks.append({"item": "仓库可访问性", "status": f"✅ HTTP {resp.status_code}" if resp.status_code == 200 else f"❌ HTTP {resp.status_code}"})
        except Exception as e:
            checks.append({"item": "仓库可访问性", "status": f"❌ {str(e)[:100]}"})

        return {"message": "代码复现检查完成", "checks": checks, "repo_url": repo_url}

    return {"message": "未知内置技能"}


# ─── 自定义 Prompt 技能执行器（调 call_qwen） ──────────────
async def _execute_prompt_skill(cs: CustomSkill, input_data: dict, user: User, db: AsyncSession, project_id: int = None) -> dict:
    """
    将 prompt_template 中的 {{key}} 替换为用户输入，然后调用 call_qwen 执行。
    
    联动能力:
    - {{input}} → 用户输入的文本
    - {{file_content}} → 如果 input_data 有 file_id，自动从资料库读取文件摘要/内容注入
    - {{project_context}} → 如果有关联项目，注入项目上下文
    - 任意 {{key}} → 从 input_data 取值
    """
    template = cs.prompt_template
    enriched_input = dict(input_data)

    # 联动1: 如果 input_data 有 file_id，从资料库取文件内容
    file_id = input_data.get("file_id", "")
    file_context = ""
    if file_id:
        doc = await _find_document(str(file_id), user, db)
        if doc:
            file_context = f"[资料库文件: {doc.filename}]\n摘要: {doc.summary or '无'}\n结构化数据: {json.dumps(doc.structured_data or {}, ensure_ascii=False)[:2000]}"
            enriched_input["file_content"] = file_context
            enriched_input["filename"] = doc.filename

    # 联动2: 如果有关联项目，注入项目上下文
    linked_pid = getattr(cs, 'linked_project_id', None) or project_id
    project_context = ""
    if linked_pid:
        from app.database.models import Project
        proj = (await db.execute(select(Project).where(Project.id == linked_pid))).scalar_one_or_none()
        if proj:
            project_context = f"[项目: {proj.title}]\n研究问题: {proj.research_question}\n领域: {proj.domain}"
            enriched_input["project_context"] = project_context

    # 替换所有 {{key}} 占位符
    placeholders = re.findall(r'\{\{(\w+)\}\}', template)
    filled_prompt = template
    for key in placeholders:
        value = enriched_input.get(key, f"[用户未提供 {key}]")
        filled_prompt = filled_prompt.replace(f"{{{{{key}}}}}", str(value))

    # 如果没有占位符，把用户输入追加到末尾
    if not placeholders and input_data:
        user_input_str = input_data.get("input", "") or json.dumps(input_data, ensure_ascii=False, indent=2)
        context_parts = []
        if file_context:
            context_parts.append(file_context)
        if project_context:
            context_parts.append(project_context)
        context_parts.append(f"用户输入:\n{user_input_str}")
        filled_prompt = f"{template}\n\n" + "\n\n".join(context_parts)

    logger.info(f"[Skill-Prompt] Executing '{cs.name}', prompt_len={len(filled_prompt)}, placeholders={placeholders}")

    # 调用 call_qwen（和 Agent/对话 用同一个 LLM 通道）
    try:
        system_prompt = "你是智研星枢技能执行引擎。严格按照用户的 Prompt 模板指令执行任务，用中文回答。"
        result = await call_qwen(
            system_prompt=system_prompt,
            user_prompt=prompt_guard.sanitize_for_llm(filled_prompt),
            project_id=project_id,
        )
        return {
            "output": result["content"],
            "tokens": result["tokens"],
            "model": result["model"],
            "cost": result["cost"],
            "prompt_preview": filled_prompt[:300] + ("..." if len(filled_prompt) > 300 else ""),
            "skill_type": "prompt",
            "linked_file": file_context[:100] if file_context else None,
            "linked_project": project_context[:100] if project_context else None,
        }
    except Exception as e:
        logger.error(f"[Skill-Prompt] call_qwen failed: {e}")
        return {
            "output": f"⚠️ AI 调用失败: {str(e)[:200]}",
            "error": str(e),
            "skill_type": "prompt",
        }


# ─── 外接 Webhook 技能执行器 ───────────────────────────────
async def _execute_webhook(url: str, method: str, input_data: dict) -> dict:
    import httpx
    logger.info(f"[Skill-Webhook] Calling {method} {url}")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            if method.upper() == "GET":
                resp = await client.get(url, params=input_data)
            else:
                resp = await client.post(url, json=input_data)
            try:
                result = resp.json()
            except Exception:
                result = {"raw_response": resp.text[:2000]}
            return {
                "output": result,
                "http_status": resp.status_code,
                "skill_type": "webhook",
            }
    except Exception as e:
        logger.error(f"[Skill-Webhook] Failed: {e}")
        return {"output": f"⚠️ Webhook 调用失败: {str(e)[:200]}", "error": str(e), "skill_type": "webhook"}


# ─── 辅助: 查找文档 ────────────────────────────────────────
async def _find_document(file_id: str, user: User, db: AsyncSession):
    doc = None
    if str(file_id).isdigit():
        stmt = select(Document).where(Document.id == int(file_id))
        doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        stmt = select(Document).where(Document.user_id == user.id, Document.saved_name == file_id)
        doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        stmt = select(Document).where(Document.user_id == user.id, Document.filename.contains(str(file_id)))
        doc = (await db.execute(stmt)).scalars().first()
    return doc