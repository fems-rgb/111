from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import ChatMessage
from app.agents.qwen_client import call_qwen
from app.security.prompt_guard import prompt_guard
from app.security.sanitizer import sanitize_input
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

GENERAL_SYSTEM = """你是「智研星辰」AI助手，专注人文社科学术研究。可帮助：解释概念、分析研究问题、方法论建议、文献讨论、论文写作辅助。

当用户消息中包含 [附件: xxx] 标记时，说明用户上传了研究文件，其摘要或内容已附在消息中。请：
1. 优先基于附件内容回答
2. 引用附件中的具体数据/观点时注明来源文件名
3. 如附件信息不足以回答问题，明确告知并建议补充

用中文回答，学术严谨但通俗易懂。"""

FALLBACK_REPLY = "\u26a0\ufe0f AI\u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528\uff08API Key\u672a\u914d\u7f6e\u6216\u7f51\u7edc\u5f02\u5e38\uff09\u3002\n\n\u8bf7\u68c0\u67e5 backend/.env \u6587\u4ef6\u4e2d QWEN_API_KEY \u662f\u5426\u5df2\u6b63\u786e\u8bbe\u7f6e\u3002"


async def chat_with_ai(db: AsyncSession, user_id: int, content: str, project_id: int = None) -> dict:
    is_safe, reason = prompt_guard.check(content)
    if not is_safe:
        raise ValueError(f"\u5b89\u5168\u68c0\u6d4b\u672a\u901a\u8fc7: {reason}")
    content = sanitize_input(content)

    if not settings.QWEN_API_KEY or settings.QWEN_API_KEY == "sk-your-api-key-here":
        logger.warning("QWEN_API_KEY not configured, returning fallback")
        user_msg = ChatMessage(project_id=project_id, user_id=user_id, role="user", content=content)
        ai_msg = ChatMessage(project_id=project_id, user_id=user_id, role="assistant", content=FALLBACK_REPLY, tokens_used=0)
        db.add_all([user_msg, ai_msg])
        await db.commit()
        return {"reply": FALLBACK_REPLY, "tokens": {"input": 0, "output": 0}, "model": "fallback", "cost": 0}

    history = ""
    if project_id:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.project_id == project_id).order_by(ChatMessage.created_at.desc()).limit(10)
        )
        for msg in reversed(result.scalars().all()):
            history += f"\n{msg.role}: {msg.content[:500]}"

    user_prompt = f"\u5386\u53f2\u5bf9\u8bdd:\n{history}\n\n\u5f53\u524d\u95ee\u9898: {content}" if history else content

    try:
        result = await call_qwen(GENERAL_SYSTEM, prompt_guard.sanitize_for_llm(user_prompt), project_id=project_id)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        error_reply = f"\u26a0\ufe0f AI\u8c03\u7528\u5931\u8d25: {str(e)[:200]}"
        user_msg = ChatMessage(project_id=project_id, user_id=user_id, role="user", content=content)
        ai_msg = ChatMessage(project_id=project_id, user_id=user_id, role="assistant", content=error_reply, tokens_used=0)
        db.add_all([user_msg, ai_msg])
        await db.commit()
        return {"reply": error_reply, "tokens": {"input": 0, "output": 0}, "model": "error", "cost": 0}

    user_msg = ChatMessage(project_id=project_id, user_id=user_id, role="user", content=content)
    ai_msg = ChatMessage(project_id=project_id, user_id=user_id, role="assistant", content=result["content"],
                         tokens_used=result["tokens"]["input"] + result["tokens"]["output"])
    db.add_all([user_msg, ai_msg])
    await db.commit()
    return {"reply": result["content"], "tokens": result["tokens"], "model": result["model"], "cost": result["cost"]}


async def get_chat_history(db: AsyncSession, user_id: int, project_id: int = None, limit: int = 50) -> list:
    query = select(ChatMessage).where(ChatMessage.user_id == user_id)
    if project_id:
        query = query.where(ChatMessage.project_id == project_id)
    result = await db.execute(query.order_by(ChatMessage.created_at.desc()).limit(limit))
    return list(reversed(result.scalars().all()))

async def _handle_skill_command(db: AsyncSession, user_id: int, command: str, project_id: int = None) -> dict:
    """
    在 AI 对话中通过 /skill 命令调用技能市场
    用法:
      /skill literature_summary file_id=123
      /skill custom_1 input=帮我分析这段文字
      /skill data_cleaning file_id=abc.csv method=zscore
    """
    import re
    from sqlalchemy import select
    from app.database.models import CustomSkill, ChatMessage

    parts = command[len("/skill "):].strip().split(None, 1)
    skill_id = parts[0] if parts else ""
    args_str = parts[1] if len(parts) > 1 else ""

    # 解析 key=value 参数
    input_data = {}
    if args_str:
        # 先尝试提取 input=xxx (可能包含空格)
        input_match = re.search(r'input=(.+?)(?:\s+\w+=|$)', args_str)
        if input_match:
            input_data["input"] = input_match.group(1).strip()
            args_str = args_str[:input_match.start()] + args_str[input_match.end():]
        # 解析其他 key=value
        for kv in re.findall(r'(\w+)=(\S+)', args_str):
            input_data[kv[0]] = kv[1]

    if not skill_id:
        # 列出可用技能
        from app.api.v1.skills import BUILTIN_SKILLS
        builtin_list = "\n".join([f"  - {s['id']}: {s['name']} - {s['description']}" for s in BUILTIN_SKILLS.values()])
        custom_stmt = select(CustomSkill).where((CustomSkill.user_id == user_id) | (CustomSkill.is_public == True))
        customs = (await db.execute(custom_stmt)).scalars().all()
        custom_list = "\n".join([f"  - custom_{c.id}: {c.name} - {c.description}" for c in customs]) if customs else "  (无自定义技能)"

        reply = f"📋 **可用技能列表**\n\n**内置技能:**\n{builtin_list}\n\n**自定义技能:**\n{custom_list}\n\n💡 用法: `/skill <技能ID> input=你的输入`"
        user_msg = ChatMessage(project_id=project_id, user_id=user_id, role="user", content=command)
        ai_msg = ChatMessage(project_id=project_id, user_id=user_id, role="assistant", content=reply, tokens_used=0)
        db.add_all([user_msg, ai_msg])
        await db.commit()
        return {"reply": reply, "tokens": {"input": 0, "output": 0}, "model": "skill-list", "cost": 0}

    # 调用技能执行引擎
    try:
        from app.api.v1.skills import run_skill, SkillRunRequest
        from app.database.models import User
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        req = SkillRunRequest(skill_id=skill_id, input_data=input_data, project_id=project_id)
        result = await run_skill(req, user, db)

        result_data = result.get("result", {})
        output = result_data.get("output", "") or result_data.get("summary", "") or result_data.get("message", "") or json.dumps(result_data, ensure_ascii=False, indent=2)

        reply = f"🛠️ **技能执行结果** [{result.get('skill_name', skill_id)}]\n\n{output}"
        if result_data.get("tokens"):
            t = result_data["tokens"]
            reply += f"\n\n---\n📊 Token: {t.get('input',0)+t.get('output',0)} | 模型: {result_data.get('model','')} | 成本: ¥{result_data.get('cost',0):.4f}"

    except Exception as e:
        reply = f"⚠️ 技能执行失败: {str(e)[:200]}"

    user_msg = ChatMessage(project_id=project_id, user_id=user_id, role="user", content=command)
    ai_msg = ChatMessage(project_id=project_id, user_id=user_id, role="assistant", content=reply, tokens_used=0)
    db.add_all([user_msg, ai_msg])
    await db.commit()
    return {"reply": reply, "tokens": {"input": 0, "output": 0}, "model": "skill-exec", "cost": 0}