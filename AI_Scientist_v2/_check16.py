TPL = r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\templates\challenge_cup_template.html"
lines = open(TPL, encoding="utf-8").read().split("\n")
print("修复后 L5-36:")
for i in range(4, 36):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:140]))
