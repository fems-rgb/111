"""智研星枢 - 文件读写工具"""
import aiofiles
import os
import logging
from app.config import settings
from app.security.sanitizer import sanitize_filename
from app.observability.tracer import Tracer

logger = logging.getLogger(__name__)


async def save_output(project_id: int, filename: str, content: str) -> dict:
    span = Tracer.create_span("tool_call", "文件保存", project_id=project_id)
    safe = sanitize_filename(filename)
    d = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
    os.makedirs(d, exist_ok=True)
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
    path = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}", safe)
    if not os.path.exists(path):
        return {"success": False, "error": "文件不存在"}
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}