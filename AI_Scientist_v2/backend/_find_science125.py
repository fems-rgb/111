import sys, os, json
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

root = r'D:\AI_Scientist\AI_Scientist'

print('='*60)
print('🔍 Step 1: 搜索项目中 science_125 相关文件')
print('='*60)
found = []
for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'dist', '.venv']]
    for fname in files:
        fp = os.path.join(dirpath, fname)
        rel = os.path.relpath(fp, root)
        # 搜索文件名或内容包含 science_125 / 125个问题
        if 'science_125' in fname.lower() or 'seed' in fname.lower() or 'question' in fname.lower():
            found.append(rel)
        elif fname.endswith(('.json', '.csv', '.yaml', '.yml', '.txt')):
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000)
                    if 'science_125' in content or '125' in content and ('science' in content.lower() or 'question' in content.lower()):
                        found.append(rel)
            except:
                pass

if found:
    for f in sorted(set(found)):
        print(f'   📄 {f}')
else:
    print('   ❌ 未找到 science_125 相关数据文件')

print(f'\n{"="*60}')
print('🔍 Step 2: 查看 questions API 中如何引用 source=science_125')
print('='*60)
q_api = os.path.join(root, 'backend', 'app', 'api', 'v1', 'questions.py')
if os.path.exists(q_api):
    with open(q_api, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if 'science_125' in line or 'seed' in line.lower() or 'init' in line.lower() or 'default' in line.lower():
                start = max(0, i-3)
                end = min(999, i+5)
                lines = open(q_api, 'r', encoding='utf-8').readlines()
                for j in range(start, min(end, len(lines))):
                    marker = '>>>' if j == i-1 else '   '
                    print(f'   {marker} L{j+1}: {lines[j]}', end='')
                print()
else:
    print(f'   ❌ {q_api} 不存在')

print(f'\n{"="*60}')
print('🔍 Step 3: 查看 models.py 中 ScienceQuestion.source 默认值')
print('='*60)
models_path = os.path.join(root, 'backend', 'app', 'database', 'models.py')
with open(models_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    in_sq = False
    for i, line in enumerate(lines):
        if 'class ScienceQuestion' in line:
            in_sq = True
        if in_sq:
            print(f'   L{i+1}: {line}', end='')
            if line.strip().startswith('class ') and 'ScienceQuestion' not in line:
                break

