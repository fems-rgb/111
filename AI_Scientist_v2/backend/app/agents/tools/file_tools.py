"""智研星枢 - 文件读写工具（Agent 产物固定落 backend/generated/agent_output/）"""
import aiofiles
import os
import logging
from app.security.sanitizer import sanitize_filename
from app.observability.tracer import Tracer
from app.utils import paths

logger = logging.getLogger(__name__)


def _out_dir(project_id: int) -> str:
    return str(paths.gen_dir("agent_output", f"project_{project_id}"))


async def save_output(project_id: int, filename: str, content: str) -> dict:
    span = Tracer.create_span("tool_call", "文件保存", project_id=project_id)
    safe = sanitize_filename(filename)
    d = _out_dir(project_id)
    path = os.path.join(d, safe)
    try:
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content)
        result = {"success": True, "path": path, "size": len(content)}
        span.set_output(result)
        Tracer.finish_span(span)
        return result
    except Exception as e:
        span.set_error(str(e))
        Tracer.finish_span(span)
        return {"success": False, "error": str(e)}


async def read_output(project_id: int, filename: str) -> dict:
    safe = sanitize_filename(filename)
    path = os.path.join(_out_dir(project_id), safe)
    if not os.path.exists(path):
        # 历史遗留：早期 Agent 产物写在 uploads/project_{id}/
        legacy = os.path.join(str(paths.UPLOADS_ROOT), f"project_{project_id}", safe)
        if not os.path.exists(legacy):
            return {"success": False, "error": "文件不存在"}
        path = legacy
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}