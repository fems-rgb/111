# -*- coding: utf-8 -*-
"""清理 <body> 里第二个 <style> 块的 nowrap 残留 + 补 table-layout:fixed"""
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
src = open(TPL, encoding="utf-8").read()

fixes = [
    # body 里 th 的 nowrap
    (
        '  th { background: #e8eaf6; white-space: nowrap; }',
        '  th { background: #e8eaf6; white-space: normal; overflow-wrap: anywhere; }'
    ),
    # body 里的 table 规则补 fixed
    (
        '  table { page-break-inside: auto; border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9.5pt; }',
        '  table { page-break-inside: auto; border-collapse: collapse; table-layout: fixed; width: 100%; max-width: 100%; margin: 8px 0; font-size: 9.5pt; overflow-wrap: anywhere; }'
    ),
]
for old, new in fixes:
    if old in src:
        src = src.replace(old, new, 1)
        print("[修改]", old.strip()[:55])
    else:
        print("[跳过]", old.strip()[:55])

open(TPL, "w", encoding="utf-8").write(src)

# 复核
final = open(TPL, encoding="utf-8").read()
print()
print("  nowrap 残留次数:", final.count("white-space: nowrap"))
print("  table-layout:fixed 次数:", final.count("table-layout: fixed"))
