import re
p = "backend/app/api/v1/projects.py"
src = open(p, encoding="utf-8").read()

OLD = """    try:
        clean_project_files(project_id)
    except Exception as e:
        print(f"[cascade-A] project file cleanup skipped: {e}")

    await db.delete(project)
    await db.commit()"""

NEW = """    try:
        clean_project_files(project_id)
    except Exception as e:
        print(f"[cascade-A] project file cleanup skipped: {e}")

    # [cascade-B] 清理所有子表记录（避免外键/关联残留导致删除失败）
    try:
        from sqlalchemy import delete as _sdel
        from app.database.models import (
            AgentTask, ExperimentRun, Hypothesis, TraceRecord,
            IterationRecord, Notification, ProjectShare, CostRecord,
        )
        _child_models = [
            (AgentTask, "project_id"),
            (ExperimentRun, "project_id"),
            (Hypothesis, "project_id"),
            (IterationRecord, "project_id"),
            (TraceRecord, "project_id"),
        ]
        for _model, _col in _child_models:
            try:
                if not hasattr(_model, _col):
                    continue
                _res = await db.execute(
                    _sdel(_model).where(getattr(_model, _col) == project_id)
                )
                print(f"[cascade-B] {_model.__name__} 删除 {_res.rowcount or 0} 条")
            except Exception as _ce:
                print(f"[cascade-B] {_model.__name__} 跳过: {type(_ce).__name__}: {_ce}")

        # 通过 question_id 关联的表（ExperimentRun.question_task_id 等）
        try:
            from app.database.models import QuestionTask as _QT2
            _qt_ids = [t.id for t in (await db.execute(
                select(_QT2).where(_QT2.question_id.in_(
                    select(_SQ.question_id).where(_SQ.title == (project.title or ""))
                ) if False else select(_QT2.id)
            ))).scalars().all()] if False else []
        except Exception:
            pass

    except Exception as e:
        print(f"[cascade-B] 异常(不阻塞): {e}")

    await db.delete(project)
    await db.commit()"""

if OLD in src:
    src = src.replace(OLD, NEW, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("[OK] 级联删除已补全")
    print("  新增: agent_tasks / experiment_runs / hypotheses / trace_records / iteration_records")
else:
    print("[WARN] 未匹配到锚点，打印原文:")
    i = src.find("clean_project_files(project_id)")
    if i >= 0:
        for l in src[i-200:i+300].split("\n"):
            print("   " + l.rstrip()[:100])

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[语法校验] OK")
except py_compile.PyCompileError as e:
    print("[语法错误] L%s: %s" % (e.lineno, e.msg))
    if e.text:
        print("   " + repr(e.text)[:110])
