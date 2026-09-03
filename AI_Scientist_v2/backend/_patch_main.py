import re, pathlib

p = pathlib.Path(r'D:\AI_Scientist\AI_Scientist\backend\app\main.py')
src = p.read_text(encoding='utf-8')

# 1. 确保 import engine, Base, models
needed = [
    'from app.database.session import engine, Base',
    'from app.database import models  # noqa: F401',
]
for imp in needed:
    if imp not in src:
        src = src.replace(
            'from app.database.init_db import init_database',
            f'from app.database.init_db import init_database\n{imp}'
        )

# 2. 在 lifespan 中追加 create_all（在 await init_database() 之后）
if 'Base.metadata.create_all' not in src:
    src = src.replace(
        '    await init_database()\n    yield',
        '    await init_database()\n'
        '    # 确保所有 ORM 模型对应的表都存在\n'
        '    async with engine.begin() as conn:\n'
        '        await conn.run_sync(Base.metadata.create_all)\n'
        '    yield'
    )

# 3. 将 on_event("startup") 中的逻辑合并进 lifespan，删除废弃装饰器
old_startup = '''@app.on_event("startup")
async def _startup_scheduler():
    """启动时：注册定时任务 + 清理僵尸"""
    register_pipeline_jobs()
    # 清理后端重启残留的 running 状态任务/流水线
    from app.database.session import AsyncSessionLocal
    from app.agents.orchestrator import orchestrator
    async with AsyncSessionLocal() as db:
        await orchestrator.cleanup_zombies(db)'''

new_in_lifespan = '''    # 注册定时任务 + 清理僵尸（从旧 on_event 迁移）
    register_pipeline_jobs()
    from app.database.session import AsyncSessionLocal
    from app.agents.orchestrator import orchestrator
    async with AsyncSessionLocal() as db:
        await orchestrator.cleanup_zombies(db)
    yield'''

if old_startup in src:
    # 替换 lifespan 中最后一个 yield 为带 scheduler 的版本
    src = src.replace('    yield\n', new_in_lifespan + '\n', 1)
    # 删除旧的 on_event 块
    src = src.replace('\n\n' + old_startup, '')
    # 如果前面还有空行残留，清理一下
    src = re.sub(r'\n{3,}', '\n\n', src)

p.write_text(src, encoding='utf-8')
print('✅ main.py patched successfully')
print('=' * 60)
print(p.read_text(encoding='utf-8'))
