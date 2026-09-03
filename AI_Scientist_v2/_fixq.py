import re
p = "backend/app/api/v1/questions.py"
src = open(p, encoding="utf-8").read()

HELPER = '''

def _real_task_progress(db, task) -> int:
    """[动态进度] 用关联 project 的 agent_tasks 完成比例计算真实进度。
    不写死任何数字；查不到关联时返回 None（由调用方保留原值）。
    """
    try:
        from app.database.models import Project, AgentTask
        from sqlalchemy import select as _sel
        qid = getattr(task, "question_id", None)
        if qid is None:
            return None
        rows = db.query(AgentTask.project_id, AgentTask.status).filter(
            AgentTask.project_id.in_(
                db.query(Project.id).filter(Project.title.like("[题库]%"))
            )
        ).all()
        # 用 question_id 精确关联：Project.title 含该题目标题
        from app.database.models import ScienceQuestion
        sq = db.query(ScienceQuestion).filter(ScienceQuestion.question_id == qid).first()
        if not sq or not getattr(sq, "title", None):
            return None
        prows = db.query(Project.id).filter(Project.title == "[题库] " + str(sq.title)[:80]).all()
        if not prows:
            prows = db.query(Project.id).filter(Project.title.like("%" + str(sq.title)[:24] + "%")).all()
        if not prows:
            return None
        pids = [r[0] for r in prows]
        tasks = db.query(AgentTask.status).filter(AgentTask.project_id.in_(pids)).all()
        if not tasks:
            return None
        total = len(tasks)
        done = sum(1 for (st,) in tasks if str(
            st.value if hasattr(st, "value") else st
        ).strip().lower() in ("completed", "complete", "done", "success", "succeeded"))
        return round(done / total * 100)
    except Exception:
        return None

'''

if "_real_task_progress" not in src:
    m = re.search(r"^@router\.", src, re.M)
    if m:
        src = src[:m.start()] + HELPER.lstrip("\n") + src[m.start():]
        open(p, "w", encoding="utf-8").write(src)
        print("[1] OK: _real_task_progress 已注入")
    else:
        src = src + HELPER
        open(p, "w", encoding="utf-8").write(src)
        print("[1] 追加到末尾")
else:
    print("[1] 已存在")

# 把写死的 task.progress = 30 改为动态计算
src = open(p, encoding="utf-8").read()
pat = re.compile(r"^(\s*)task\.progress\s*=\s*30\s*$", re.M)
n30 = len(pat.findall(src))
src = pat.sub(lambda m: m.group(1) + "_rp = _real_task_progress(db, task)\n"
              + m.group(1) + "task.progress = _rp if _rp is not None else 30", src)

pat10 = re.compile(r"^(\s*)task\.progress\s*=\s*10\s*$", re.M)
pat10.sub(lambda m: m.group(1) + "_rp = _real_task_progress(db, task)\n"
          + m.group(1) + "task.progress = _rp if _rp is not None else 10", src)

open(p, "w", encoding="utf-8").write(src)
print("[2] 替换硬编码 progress=30 共 %d 处" % n30)

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[3] syntax OK")
except py_compile.PyCompileError as e:
    print("[3] 语法错误 L%s: %s" % (e.lineno, e.msg))
