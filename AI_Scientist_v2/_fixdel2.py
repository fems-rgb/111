p = "backend/app/api/v1/projects.py"
src = open(p, encoding="utf-8").read()

# 补 import
old_imp = """        from app.database.models import (
            AgentTask, ExperimentRun, Hypothesis, TraceRecord,
            IterationRecord, Notification, ProjectShare, CostRecord,
        )"""
new_imp = """        from app.database.models import (
            AgentTask, ExperimentRun, Hypothesis, TraceRecord,
            IterationRecord, Notification, ProjectShare, CostRecord,
            ChatMessage, CustomSkill,
        )"""
if old_imp in src:
    src = src.replace(old_imp, new_imp, 1)
    print("[1] OK: import 已补 ChatMessage / CustomSkill")
else:
    print("[1] import 已含或格式不同，跳过")

# 补 _child_models
old_list = """        _child_models = [
            (AgentTask, "project_id"),
            (ExperimentRun, "project_id"),
            (Hypothesis, "project_id"),
            (IterationRecord, "project_id"),
            (TraceRecord, "project_id"),
        ]"""
new_list = """        _child_models = [
            (AgentTask, "project_id"),
            (ExperimentRun, "project_id"),
            (Hypothesis, "project_id"),
            (IterationRecord, "project_id"),
            (TraceRecord, "project_id"),
            (CostRecord, "project_id"),
            (ChatMessage, "project_id"),
            (CustomSkill, "project_id"),
            (ProjectShare, "project_id"),
        ]"""
if old_list in src:
    src = src.replace(old_list, new_list, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("[2] OK: 子表清单已补全（9 张表）")
elif new_list in src:
    print("[2] 已是完整版，无需修改")
else:
    print("[2] WARN: 未匹配，需手动确认")

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[3] syntax OK")
except py_compile.PyCompileError as e:
    print("[3] 语法错误 L%s: %s" % (e.lineno, e.msg))
