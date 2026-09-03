# -*- coding: utf-8 -*-
"""修复 proposal_addon.py:194 —— 补传 research_question"""
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\proposal_addon.py"
src = open(p, encoding="utf-8").read()

old = """        from app.api.v1.export import generate_challenge_cup_pdf
        case_pdf = generate_challenge_cup_pdf(project_id)"""
new = """        from app.api.v1.export import generate_challenge_cup_pdf
        _rq = ""
        if 'proj' in dir() and proj is not None:
            _rq = getattr(proj, "research_question", "") or getattr(proj, "description", "")
        case_pdf = generate_challenge_cup_pdf(project_id, research_question=_rq)"""
if old in src:
    src = src.replace(old, new, 1)
    print("[修改] proposal_addon.py:194 补传 research_question")
else:
    print("[跳过] 锚点未匹配（检查 L193-194 原文）")

open(p, "w", encoding="utf-8").write(src)
import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] OK")
except py_compile.PyCompileError as e:
    print(f"[syntax] L{e.lineno}: {e.msg}")
