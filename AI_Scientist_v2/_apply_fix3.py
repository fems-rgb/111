# -*- coding: utf-8 -*-
"""修复 orchestrator.py:534 —— 补传 research_question"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
src = open(p, encoding="utf-8").read()

old = """                    _pdf = await _asyncio.get_running_loop().run_in_executor(None, _gen_pdf, project_id)"""
new = """                    _rq = ""
                    if 'project' in dir() and project is not None:
                        _rq = getattr(project, "research_question", "")
                    _pdf = await _asyncio.get_running_loop().run_in_executor(
                        None, lambda: _gen_pdf(project_id, research_question=_rq))"""
if old in src:
    src = src.replace(old, new, 1)
    print("[修改] orchestrator.py:534 补传 research_question")
else:
    print("[跳过] 锚点未匹配（检查 L534 原文）")

open(p, "w", encoding="utf-8").write(src)
import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] OK")
except py_compile.PyCompileError as e:
    print(f"[syntax] L{e.lineno}: {e.msg}")
