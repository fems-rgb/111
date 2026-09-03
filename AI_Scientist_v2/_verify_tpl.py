# -*- coding: utf-8 -*-
TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(TPL, encoding="utf-8").read().split("\n")
print("="*64)
print("修复后 L5-40 (head 样式)")
print("="*64)
for i in range(4, min(42, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:140]))

print()
print("="*64)
print("所有 table 行（确认 class + colgroup）")
print("="*64)
for i, l in enumerate(lines):
    if "<table" in l or "<colgroup>" in l:
        print("%4d| %s" % (i+1, l.rstrip()[:150]))
