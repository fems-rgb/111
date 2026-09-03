import re

with open('app/database/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# === 修复1: 在 Project 类中添加 progress 字段（在 evidence_files 之后，created_at 之前）===
old_project = '    evidence_files = Column(JSON, default=list)  # 证据文件file_id列表\n    created_at'
new_project = '    evidence_files = Column(JSON, default=list)  # 证据文件file_id列表\n    progress = Column(Integer, default=0)  # 流水线进度百分比0-100\n    created_at'

if old_project in content:
    content = content.replace(old_project, new_project)
    print('[OK] Added progress field to Project class')
else:
    print('[WARN] Could not find insertion point in Project class')

# === 修复2: 删除 pipeline_runs 类末尾错误的 progress 行 ===
# 匹配第441行那种格式
bad_progress = "\n    progress = Column(Integer, default=0, comment='流水线进度百分比0-100')"
if bad_progress in content:
    content = content.replace(bad_progress, '')
    print('[OK] Removed misplaced progress from pipeline_runs')
else:
    print('[SKIP] No misplaced progress line found')

# === 修复3: 确保文件无 BOM ===
if content.startswith('\ufeff'):
    content = content[1:]
    print('[OK] Removed BOM')

with open('app/database/models.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print('[DONE] File saved')

# === 验证语法 ===
import ast
ast.parse(content)
print('[OK] Syntax valid')

# === 验证 progress 在正确位置 ===
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'progress' in line.lower():
        print(f'  Line {i}: {line.strip()}')
