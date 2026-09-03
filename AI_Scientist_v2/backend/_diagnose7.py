import sys, os, glob
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')

root = r'D:\AI_Scientist\AI_Scientist'

print('='*60)
print('🔍 1. 查找所有 Python 入口文件')
print('='*60)
# 搜索包含 uvicorn.run 或 FastAPI() 的文件
for dirpath, dirs, files in os.walk(root):
    # 跳过 node_modules, __pycache__, .git
    dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'dist', '.venv', 'venv']]
    for fname in files:
        if fname.endswith('.py'):
            fp = os.path.join(dirpath, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    if 'uvicorn' in content or 'FastAPI()' in content or 'app = FastAPI' in content:
                        rel = os.path.relpath(fp, root)
                        print(f'\n   📄 {rel}')
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if any(kw in line for kw in ['uvicorn', 'FastAPI()', 'app = FastAPI', 'lifespan', 'on_event', 'create_all', 'init_db', 'seed']):
                                print(f'      L{i+1}: {line.strip()[:120]}')
            except:
                pass

print(f'\n{"="*60}')
print('🔍 2. 前端 localStorage / sessionStorage 使用')
print('='*60)
frontend_src = os.path.join(root, 'frontend', 'src')
for dirpath, dirs, files in os.walk(frontend_src):
    for fname in files:
        if fname.endswith(('.ts', '.js', '.vue')):
            fp = os.path.join(dirpath, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    if 'localStorage' in content or 'sessionStorage' in content:
                        rel = os.path.relpath(fp, frontend_src)
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'localStorage' in line or 'sessionStorage' in line:
                                print(f'   📄 {rel} L{i+1}: {line.strip()[:120]}')
            except:
                pass

print(f'\n{"="*60}')
print('🔍 3. 项目根目录文件列表')
print('='*60)
for item in sorted(os.listdir(root)):
    fp = os.path.join(root, item)
    ftype = 'DIR' if os.path.isdir(fp) else 'FILE'
    size = os.path.getsize(fp) if os.path.isfile(fp) else ''
    print(f'   {ftype:4s} {item} {size}')

