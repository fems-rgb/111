import re
p = "frontend/src/views/workspace/QuestionsView.vue"
lines = open(p, encoding="utf-8").read().split("\n")
print("="*60)
print("题库页 progress 数据来源 (含 t. 的关键行)")
print("="*60)
for i, l in enumerate(lines, 1):
    s = l.strip()
    if "progress" in s or "activeTask" in s or "tasks.value" in s:
        print("  L%-4d %s" % (i, s[:115]))
