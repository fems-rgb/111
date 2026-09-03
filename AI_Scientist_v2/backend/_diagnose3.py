import sys, os, asyncio
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def deep_diagnose():
    async with AsyncSessionLocal() as db:
        # 1. 查看所有 agent_tasks 的状态
        print('='*60)
        print('🔍 Step 1: 所有 agent_tasks 详情')
        print('='*60)
        rows = await db.execute(text("""
            SELECT id, agent_name, step_order, status, error_message, 
                   started_at, finished_at, tokens_used, cost_yuan,
                   LENGTH(output_data) as output_len
            FROM agent_tasks ORDER BY step_order
        """))
        for r in rows.fetchall():
            print(f'   Task#{r[0]} | {r[1]:20s} | step={r[2]} | status={r[3]:10s} | err={str(r[4])[:50]} | out_len={r[9]} | tokens={r[7]} | cost={r[8]}')
            if r[5]: print(f'          started: {r[5]}')
            if r[6]: print(f'          finished: {r[6]}')

        # 2. 查看后端日志文件
        print(f'\n{"="*60}')
        print('🔍 Step 2: 查找后端日志')
        print('='*60)
        import glob
        log_patterns = [
            r'D:\AI_Scientist\AI_Scientist\backend\*.log',
            r'D:\AI_Scientist\AI_Scientist\backend\logs\*',
            r'D:\AI_Scientist\AI_Scientist\*.log',
            r'D:\AI_Scientist\AI_Scientist\backend\app\*.log',
        ]
        for pat in log_patterns:
            files = glob.glob(pat)
            for f in files:
                size = os.path.getsize(f)
                print(f'   📄 {f} ({size} bytes)')
                if size > 0 and size < 500000:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                        lines = fh.readlines()
                        # 搜索错误/暂停相关
                        for i, line in enumerate(lines):
                            ll = line.lower()
                            if any(kw in ll for kw in ['error', 'exception', 'pause', 'paused', 'review', 'peer_review', 'failed', 'timeout']):
                                print(f'      L{i+1}: {line.rstrip()[:150]}')

        # 3. 查看流水线执行代码
        print(f'\n{"="*60}')
        print('🔍 Step 3: 查找流水线执行逻辑')
        print('='*60)
        root = r'D:\AI_Scientist\AI_Scientist\backend'
        pipeline_files = []
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.venv', 'node_modules']]
            for fname in files:
                if fname.endswith('.py'):
                    fp = os.path.join(dirpath, fname)
                    rel = os.path.relpath(fp, root)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'peer_review' in content or 'review' in content.lower() and 'pipeline' in content.lower():
                                if 'pipeline' in fname.lower() or 'runner' in fname.lower() or 'executor' in fname.lower() or 'engine' in fname.lower() or 'orchestrat' in fname.lower() or 'question' in fname.lower():
                                    pipeline_files.append((rel, fp, content))
                    except:
                        pass
        
        for rel, fp, content in pipeline_files:
            print(f'\n   📄 {rel} ({len(content)} chars)')
            lines = content.split('\n')
            for i, line in enumerate(lines):
                ll = line.lower()
                if any(kw in ll for kw in ['peer_review', 'review', 'pause', 'paused', 'step_order == 8', 'step == 8', 'requires_review']):
                    start = max(0, i-2)
                    end = min(len(lines), i+5)
                    for j in range(start, end):
                        marker = '>>>' if j == i else '   '
                        print(f'      {marker} L{j+1}: {lines[j][:120]}')
                    print()

asyncio.run(deep_diagnose())
