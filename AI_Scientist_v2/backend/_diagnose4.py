import sys, os, asyncio
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def confirm():
    async with AsyncSessionLocal() as db:
        # 1. 计算总 token 消耗
        print('='*60)
        print('🔍 Token 累计统计')
        print('='*60)
        rows = await db.execute(text("SELECT agent_name, step_order, tokens_used, cost_yuan FROM agent_tasks ORDER BY step_order"))
        total_tokens = 0
        total_cost = 0.0
        for r in rows.fetchall():
            total_tokens += (r[2] or 0)
            total_cost += (r[3] or 0.0)
            print(f'   {r[0]:20s} step={r[1]} tokens={r[2]:>6} cost={r[3]:.4f}')
        print(f'\n   📊 总计: tokens={total_tokens}, cost={total_cost:.4f}')
        
        # 2. 查看 orchestrator 的 TOKEN_BUDGET 和 GLOBAL_TIMEOUT
        print(f'\n{"="*60}')
        print('🔍 Orchestrator 限制参数')
        print('='*60)
        orch_path = r'D:\AI_Scientist\AI_Scientist\backend\app\agents\orchestrator.py'
        with open(orch_path, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line for kw in ['TOKEN_BUDGET', 'GLOBAL_TIMEOUT', 'MAX_TOKENS']):
                print(f'   L{i+1}: {line.strip()}')

        # 3. 查看日志中关于暂停的记录
        print(f'\n{"="*60}')
        print('🔍 日志中的暂停/超时/预算记录')
        print('='*60)
        log_path = r'D:\AI_Scientist\AI_Scientist\backend\logs\app_20260825.log'
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 文件很大(19MB)，只读最后部分
                f.seek(max(0, os.path.getsize(log_path) - 200000))
                tail = f.read()
            
            for line in tail.split('\n'):
                ll = line.lower()
                if any(kw in ll for kw in ['paused', 'timeout', 'token budget', 'budget exceeded', 'global timeout', 'running flag', 'recovered', 'zombie', 'orchestrator']):
                    print(f'   {line.rstrip()[:180]}')
        except Exception as e:
            print(f'   Error reading log: {e}')

        # 4. 查看 _running_projects 机制
        print(f'\n{"="*60}')
        print('🔍 _running_projects 相关代码')
        print('='*60)
        for i, line in enumerate(lines):
            if '_running_projects' in line:
                print(f'   L{i+1}: {line.rstrip()[:120]}')

asyncio.run(confirm())
