"""智研星枢 - 安全代码执行沙箱"""
import asyncio
import tempfile
import os
import logging
from app.observability.tracer import Tracer

logger = logging.getLogger(__name__)
FORBIDDEN = ["os.system", "subprocess", "shutil.rmtree", "__import__", "eval(", "exec("]
FORBIDDEN_MODS = ["socket", "ctypes", "multiprocessing"]


async def execute_python(code: str, timeout: int = 30, project_id: int = None) -> dict:
    span = Tracer.create_span("tool_call", "代码执行", project_id=project_id)
    span.set_input({"code": code[:2000]})
    for f in FORBIDDEN:
        if f in code:
            span.set_error(f"安全拦截: {f}")
            Tracer.finish_span(span)
            return {"success": False, "output": "", "error": f"禁止使用 {f}"}
    for m in FORBIDDEN_MODS:
        if f"import {m}" in code or f"from {m}" in code:
            span.set_error(f"安全拦截: {m}")
            Tracer.finish_span(span)
            return {"success": False, "output": "", "error": f"禁止导入 {m}"}
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            tmp = f.name
        proc = await asyncio.create_subprocess_exec("python", tmp, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            result = {"success": proc.returncode == 0, "output": stdout.decode('utf-8', errors='replace')[:5000],
                      "error": stderr.decode('utf-8', errors='replace')[:2000]}
        except asyncio.TimeoutError:
            proc.kill()
            result = {"success": False, "output": "", "error": f"超时({timeout}s)"}
        os.unlink(tmp)
        span.set_output(result)
        Tracer.finish_span(span)
        return result
    except Exception as e:
        span.set_error(str(e))
        Tracer.finish_span(span)
        return {"success": False, "output": "", "error": str(e)}