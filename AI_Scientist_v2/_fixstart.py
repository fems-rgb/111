p = "backend/app/agents/orchestrator.py"
src = open(p, encoding="utf-8").read()

print("="*64)
print("修改前 start_project (L39 签名 + L75-98 重建逻辑)")
print("="*64)
lines = src.split("\n")
for i in range(38, 100):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:120]))

# 1) 函数签名加 resume_mode=False
old_sig = "async def start_project(self, db: AsyncSession, project_id: int, user_id: int, custom_pipeline: list[str] | None = None):"
new_sig = """async def start_project(self, db: AsyncSession, project_id: int, user_id: int,
                         custom_pipeline: list[str] | None = None, resume_mode: bool = False):"""
if old_sig in src:
    src = src.replace(old_sig, new_sig, 1)
    print("\n[OK] 签名已加 resume_mode=False")
else:
    print("\n[WARN] 签名锚点未匹配")

# 2) 在 "for t in existing" 删除逻辑前，加 resume_mode 分支
old_del = """        existing = await db.execute(select(AgentTask).where(AgentTask.project_id == project_id))
        for t in existing.scalars().all():
            await db.delete(t)
        await db.flush()"""
new_del = """        existing = await db.execute(select(AgentTask).where(AgentTask.project_id == project_id))
        if resume_mode:
            # 继续模式：保留已完成/已生成的 task，只重置 RUNNING/FAILED 的为非阻塞状态
            for t in existing.scalars().all():
                if t.status in (TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.WAITING_REVIEW):
                    t.status = TaskStatus.PENDING
            await db.flush()
        else:
            # 全新启动：清空所有 task 重建
            for t in existing.scalars().all():
                await db.delete(t)
            await db.flush()"""
if old_del in src:
    src = src.replace(old_del, new_del, 1)
    print("[OK] 删除逻辑已加 resume_mode 分支（保留已完成 task）")
else:
    print("[WARN] 删除逻辑锚点未匹配，尝试宽松匹配...")
    # 宽松：逐行找
    if "for t in existing.scalars().all():" in src:
        print("  (存在 existing 循环，请手动在 L76 前加 resume_mode 判断)")

open(p, "w", encoding="utf-8").write(src)
import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("[syntax] orchestrator.py OK")
except py_compile.PyCompileError as e:
    print("[syntax] L%d: %s" % (e.lineno, e.msg))
