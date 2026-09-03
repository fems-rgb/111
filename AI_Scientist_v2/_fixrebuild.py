p = "backend/app/agents/orchestrator.py"
src = open(p, encoding="utf-8").read()

print("="*64)
print("修改前 L86-112")
print("="*64)
lines = src.split("\n")
for i in range(85, 113):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:140]))

# 把 L88-106（重建循环 + commit）包进 else 分支
# 锚点：从 "        tasks = []" 到 "        await db.commit()\n        project.status = ProjectStatus.RUNNING"
old = """        tasks = []
        for i, agent_name in enumerate(agent_sequence):
            agent_cls = AGENT_REGISTRY.get(agent_name)
            if not agent_cls:
                continue
            agent = agent_cls()
            # 默认全自主一条龙: 除非 project.config.review_steps 明确列出该 agent, 否则不审核
            _proj_cfg = (project.config or {}) if hasattr(project, "config") and project.config else {}
            _review_steps = _proj_cfg.get("review_steps", []) if isinstance(_proj_cfg, dict) else []
            _need_review = agent_name in _review_steps
            task = AgentTask(project_id=project_id, agent_name=agent_name, step_order=i+1,
                             status=TaskStatus.PENDING,
                             requires_review=_need_review,
                             max_retries=(3 if mode == "expert" else agent.max_retries),
                             model_used=route_result["suggested_model"])
            db.add(task)
            tasks.append(task)

        await db.commit()
        project.status = ProjectStatus.RUNNING"""

new = """        if resume_mode:
            # 继续模式：task 列表已保留（L76-81 重置了 RUNNING/FAILED），
            # 直接复用现有 task，不重建
            result = await db.execute(
                select(AgentTask).where(AgentTask.project_id == project_id).order_by(AgentTask.step_order)
            )
            tasks = result.scalars().all()
            project.status = ProjectStatus.RUNNING
            await db.commit()
        else:
            # 全新启动：重建 task 列表
            tasks = []
            for i, agent_name in enumerate(agent_sequence):
                agent_cls = AGENT_REGISTRY.get(agent_name)
                if not agent_cls:
                    continue
                agent = agent_cls()
                # 默认全自主一条龙: 除非 project.config.review_steps 明确列出该 agent, 否则不审核
                _proj_cfg = (project.config or {}) if hasattr(project, "config") and project.config else {}
                _review_steps = _proj_cfg.get("review_steps", []) if isinstance(_proj_cfg, dict) else []
                _need_review = agent_name in _review_steps
                task = AgentTask(project_id=project_id, agent_name=agent_name, step_order=i+1,
                                 status=TaskStatus.PENDING,
                                 requires_review=_need_review,
                                 max_retries=(3 if mode == "expert" else agent.max_retries),
                                 model_used=route_result["suggested_model"])
                db.add(task)
                tasks.append(task)

            await db.commit()
            project.status = ProjectStatus.RUNNING"""

if old in src:
    src = src.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("\n[OK] 重建循环已包进 else，resume_mode 时复用现有 task")
else:
    print("\n[WARN] 精确锚点未匹配（可能已有缩进/空格差异）")
    print("尝试宽松方式：在 L88 'tasks = []' 前加 '    if not resume_mode:' ...")

import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] OK")
except py_compile.PyCompileError as e:
    print("[syntax] L%d: %s" % (e.lineno, e.msg))
