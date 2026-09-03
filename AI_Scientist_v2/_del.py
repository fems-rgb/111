import re
src = open("backend/app/api/v1/projects.py", encoding="utf-8").read()
lines = src.split("\n")
start = None
for i, l in enumerate(lines):
    if "@router.delete" in l:
        start = i
        break
if start is None:
    print("未找到 delete 路由")
else:
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("@router.") or (s.startswith("def ") and j > start + 3):
            end = j
            break
    print("="*60)
    print("删除接口 (行 %d-%d)" % (start+1, end))
    print("="*60)
    for i in range(start, min(end, start+70)):
        print("%4d| %s" % (i+1, lines[i].rstrip()[:110]))
