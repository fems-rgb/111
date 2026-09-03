import sys, os
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')

root = r'D:\AI_Scientist\AI_Scientist'

print('='*60)
print('🔧 Step 1: 查看当前 config.py 中 DATABASE_URL 的定义方式')
print('='*60)
config_path = os.path.join(root, 'backend', 'app', 'config.py')
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'DATABASE' in line or 'database' in line.lower() or '.env' in line.lower() or 'BaseSettings' in line or 'model_config' in line:
            start = max(0, i-1)
            end = min(len(lines), i+3)
            for j in range(start, end):
                marker = '>>>' if j == i else '   '
                print(f'   {marker} L{j+1}: {lines[j]}')

# 查找 .env 文件
print(f'\n{"="*60}')
print('🔍 Step 2: 查找所有 .env 文件')
print('='*60)
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'dist']]
    for fname in files:
        if fname.startswith('.env'):
            fp = os.path.join(dirpath, fname)
            rel = os.path.relpath(fp, root)
            print(f'\n   📄 {rel}:')
            with open(fp, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        print(f'      {line}')

print(f'\n{"="*60}')
print('🔍 Step 3: 确认 run.py 的工作目录')
print('='*60)
run_path = os.path.join(root, 'backend', 'run.py')
with open(run_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        print(f'{i:3d} | {line}', end='')

