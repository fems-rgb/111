# -*- coding: utf-8 -*-
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(TPL, encoding="utf-8").read().split("\n")

print("L14-18 原始内容:")
for i in range(13, 18):
    print("  L%d| %r" % (i+1, lines[i]))

old = '  /* fix_v17 */ }'
if old in [l.strip() for l in lines] or any("fix_v17" in l for l in lines):
    print("\n[修复] 移除孤立 }")
    new_lines = []
    for l in lines:
        if "fix_v17" in l:
            # 只保留注释，去掉后面的 }
            new_lines.append("  /* fix_v17 */")
        else:
            new_lines.append(l)
    open(TPL, "w", encoding="utf-8").write("\n".join(new_lines))
    print("done")
else:
    print("\n[跳过] 未匹配精确文本，当前 L16:", repr(lines[15]))
