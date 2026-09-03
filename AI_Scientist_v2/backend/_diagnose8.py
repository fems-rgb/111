import sys, os
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')

root = r'D:\AI_Scientist\AI_Scientist'

print('='*60)
print('📄 backend/app/main.py 完整内容')
print('='*60)
with open(os.path.join(root, 'backend', 'app', 'main.py'), 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        print(f'{i:3d} | {line}', end='')

print(f'\n{"="*60}')
print('📄 backend/app/database/init_db.py 完整内容')
print('='*60)
init_path = os.path.join(root, 'backend', 'app', 'database', 'init_db.py')
if os.path.exists(init_path):
    with open(init_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            print(f'{i:3d} | {line}', end='')
else:
    print('   ⚠️ 文件不存在！')
    # 查找类似文件
    db_dir = os.path.join(root, 'backend', 'app', 'database')
    if os.path.exists(db_dir):
        print(f'   database/ 目录内容:')
        for f in sorted(os.listdir(db_dir)):
            print(f'      {f}')

print(f'\n{"="*60}')
print('📄 backend/app/database/session.py 完整内容')
print('='*60)
session_path = os.path.join(root, 'backend', 'app', 'database', 'session.py')
if os.path.exists(session_path):
    with open(session_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            print(f'{i:3d} | {line}', end='')

