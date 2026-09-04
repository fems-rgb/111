# -*- coding: utf-8 -*-
"""确认 [auto-export] 块的锚点是否存在"""
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\orchestrator.py"
src = open(P, encoding="utf-8").read()
print("start_marker '# [auto-export] 流水线完成' 存在?", "# [auto-export] 流水线完成" in src)
print("end_anchor 'project.final_output = context' 存在?", "project.final_output = context" in src)
# 打印锚点行号
for i, l in enumerate(src.split("\n")):
    if "# [auto-export] 流水线完成" in l or "project.final_output = context" in l:
        print(f"  L{i+1}| {l.strip()[:80]}")
