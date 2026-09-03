p = "frontend/src/views/workspace/ProjectDetail.vue"
src = open(p, encoding="utf-8").read()

print("="*64)
print("修改1: 按钮 @click")
print("="*64)
# 按钮改 handleResume
old_btn = '@click="handleStart" class="btn-primary">▶️ 继续研究'
new_btn = '@click="handleResume" class="btn-primary">▶️ 继续研究'
if old_btn in src:
    src = src.replace(old_btn, new_btn, 1)
    print("[OK] 按钮改为 handleResume")
elif "handleResume" in src:
    print("[跳过] 按钮已是 handleResume")
else:
    print("[WARN] 按钮锚点未匹配")

print()
print("="*64)
print("修改2: 添加 handleResume 函数（在 handleStart 之后）")
print("="*64)
# 在 handleStart 函数后插入 handleResume
old_start = """async function handleStart() {
  try {
    const pipeline = pipelineStore.getPipelineNames()
    await projectStore.startProject(projectId.value, pipeline.length > 0 ? pipeline : undefined)
    appStore.showToast('项目已启动', 'success')
    start()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '启动失败', 'error')
  }
}"""
new_start = """async function handleStart() {
  try {
    const pipeline = pipelineStore.getPipelineNames()
    await projectStore.startProject(projectId.value, pipeline.length > 0 ? pipeline : undefined)
    appStore.showToast('项目已启动', 'success')
    start()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '启动失败', 'error')
  }
}

async function handleResume() {
  try {
    const { projectApi } = await import('@/api/modules/project')
    await projectApi.resume(projectId.value)
    appStore.showToast('已从断点继续', 'success')
    await projectStore.fetchProject(projectId.value)
    start()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '继续失败', 'error')
  }
}"""

if "async function handleResume" in src:
    print("[跳过] handleResume 已存在")
elif old_start in src:
    src = src.replace(old_start, new_start, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("[OK] handleResume 函数已添加")
else:
    print("[WARN] handleStart 锚点未精确匹配，尝试宽松查找...")
    if "async function handleStart" in src:
        # 找到 handleStart 的结束位置（下一个空行或新函数）
        lines = src.split("\n")
        idx = None
        for i, l in enumerate(lines):
            if "async function handleStart" in l:
                idx = i
                break
        if idx:
            # 从 idx 往后找到这个函数的结束（匹配括号）
            brace_count = 0
            insert_after = idx
            for j in range(idx, len(lines)):
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count == 0 and j > idx:
                    insert_after = j
                    break
            resume_fn = """
async function handleResume() {
  try {
    const { projectApi } = await import('@/api/modules/project')
    await projectApi.resume(projectId.value)
    appStore.showToast('已从断点继续', 'success')
    await projectStore.fetchProject(projectId.value)
    start()
  } catch (e: any) {
    appStore.showToast(e.response?.data?.detail || '继续失败', 'error')
  }
}"""
            lines.insert(insert_after + 1, resume_fn.rstrip("\n"))
            src = "\n".join(lines)
            open(p, "w", encoding="utf-8").write(src)
            print("[OK] handleResume 已插入到 handleStart 之后")

# 最终校验
print()
print("="*64)
print("最终校验")
print("="*64)
final = open(p, encoding="utf-8").read()
print("  @click=\"handleResume\" 出现:", final.count('@click="handleResume"'))
print("  async function handleResume 出现:", "async function handleResume" in final)
