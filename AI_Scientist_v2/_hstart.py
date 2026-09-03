lines = open("frontend/src/views/workspace/ProjectDetail.vue", encoding="utf-8").read().split("\n")
print("="*64)
print("handleStart 实现")
print("="*64)
# 找 handleStart（在 L325 之前的某个位置，因为 L325 是 handlePause）
for i in range(260, 330):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:115]))
