import sys, os, glob, re
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')

print('='*60)
print('🔍 1. 后端启动入口 & 初始化逻辑')
print('='*60)
root = r'D:\AI_Scientist\AI_Scientist'

# 查找 main.py / app.py
for f in ['main.py', 'app.py', '__main__.py']:
    fp = os.path.join(root, 'backend', f)
    if os.path.exists(fp):
        print(f'\n📄 backend/{f}:')
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
            # 找 init / seed / startup 相关
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if any(kw in line.lower() for kw in ['init', 'seed', 'startup', 'on_event', 'lifespan', 'create_all', 'admin']):
                    start = max(0, i-1)
                    end = min(len(lines), i+3)
                    for j in range(start, end):
                        marker = '>>>' if j == i else '   '
                        print(f'   {marker} L{j+1}: {lines[j]}')

print(f'\n{"="*60}')
print('🔍 2. 前端 mock 数据搜索')
print('='*60)
frontend_src = os.path.join(root, 'frontend', 'src')
mock_keywords = ['mock', 'dummy', 'fake', 'sample', 'hardcod', '27', 'question_task']
for dirpath, dirs, files in os.walk(frontend_src):
    for fname in files:
        if fname.endswith(('.ts', '.js', '.vue')):
            fp = os.path.join(dirpath, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    for kw in mock_keywords:
                        if kw.lower() in content.lower():
                            rel = os.path.relpath(fp, frontend_src)
                            # 找到包含关键字的行
                            for i, line in enumerate(content.split('\n')):
                                if kw.lower() in line.lower():
                                    print(f'   📄 {rel} L{i+1}: {line.strip()[:100]}')
                            break
            except:
                pass

print(f'\n{"="*60}')
print('🔍 3. 后端 API 路由 - projects 和 questions')
print('='*60)
api_dir = os.path.join(root, 'backend', 'app', 'api')
if os.path.exists(api_dir):
    for dirpath, dirs, files in os.walk(api_dir):
        for fname in files:
            if fname.endswith('.py'):
                fp = os.path.join(dirpath, fname)
                rel = os.path.relpath(fp, root)
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    # 找 router 定义和关键端点
                    for i, line in enumerate(content.split('\n')):
                        if any(kw in line for kw in ['@router.', 'def get_', 'def list_', 'def create_', '/projects', '/questions', '/science']):
                            print(f'   {rel} L{i+1}: {line.strip()[:120]}')

