# ProjectDetail.vue 按钮区 + handleStart/handlePause/handleRestart 全部
lines = open("frontend/src/views/workspace/ProjectDetail.vue", encoding="utf-8").read().split("\n")
print("="*64)
print("按钮区 (L25-45) + 相关 handle 函数")
print("="*64)
for i in range(23, 60):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:115]))
print("...")
for i in range(315, 400):
    s = lines[i].rstrip()
    if s.strip().startswith("async function ") or "handleStart" in s or "handleRestart" in s or "handlePause" in s:
        print("%4d| %s" % (i+1, s[:115]))
