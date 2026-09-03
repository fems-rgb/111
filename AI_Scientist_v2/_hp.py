lines = open("frontend/src/views/workspace/ProjectDetail.vue", encoding="utf-8").read().split("\n")
print("="*64)
print("handlePause 完整实现")
print("="*64)
# 找 L325 附近
for i in range(323, min(360, len(lines))):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:110]))
