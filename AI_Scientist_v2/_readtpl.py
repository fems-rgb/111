# -*- coding: utf-8 -*-
p = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(p, encoding="utf-8").read().split("\n")
print("总行数:", len(lines))
print("="*64)
print("L1-60 (head + style)")
print("="*64)
for i in range(min(60, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:130]))

print()
print("="*64)
print("所有 <table 出现位置 + 前后上下文")
print("="*64)
for i, l in enumerate(lines):
    if "<table" in l or "</head>" in l or "<style" in l or "</style>" in l:
        print("%4d| %s" % (i+1, l.rstrip()[:140]))
