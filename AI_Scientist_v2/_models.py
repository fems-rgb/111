import re
src = open("backend/app/database/models.py", encoding="utf-8").read()
print("="*60)
print("所有模型类及其 project_id 列")
print("="*60)
cur = None
for l in src.split("\n"):
    m = re.match(r"^class (\w+)\(", l)
    if m:
        cur = m.group(1)
        print("  class %s" % cur)
    if "project_id" in l and "Column" in l:
        print("      -> project_id ✓")
