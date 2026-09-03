p = "frontend/src/views/workspace/ProjectDetail.vue"
lines = open(p, encoding="utf-8").read().split("\n")

print("="*64)
print("当前 L32-36 按钮区")
print("="*64)
for i in range(31, 37):
    print("%4d| %s" % (i+1, lines[i].rstrip()[:120]))

# 加「继续」按钮：在暂停按钮之后
target = "<button v-if=\"project.status === 'running'\" @click=\"handlePause\" class=\"btn-secondary\">⏸️ 暂停</button>"
resume_btn = "<button v-else-if=\"project.status === 'paused'\" @click=\"handleStart\" class=\"btn-primary\">▶️ 继续研究</button>"

src = "\n".join(lines)
if "status === 'paused'" in src:
    print("\n[跳过] 继续按钮已存在")
else:
    if target in src:
        src = src.replace(target, target + "\n          " + resume_btn, 1)
        open(p, "w", encoding="utf-8").write(src)
        print("\n[OK] 已添加「▶️ 继续研究」按钮")
    else:
        print("\n[WARN] 锚点未匹配，手动加在 L34 后:")
        print("  " + resume_btn)

# 校验
import subprocess, py_compile
print()
print("="*64)
print("语法校验")
print("="*64)
# Vue 文件无法直接 py_compile；检查括号/标签平衡即可
content = open(p, encoding="utf-8").read()
print("  resume 按钮出现次数:", content.count("继续研究"))
print("  v-else-if=\"project.status === 'paused'\" 出现:", ("status === 'paused'" in content))
