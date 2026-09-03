p = "frontend/src/api/modules/project.ts"
src = open(p, encoding="utf-8").read()

print("修改前 pause 行:")
for l in src.split("\n"):
    if "pause:" in l:
        print("  " + l.strip()[:120])

# 在 pause 后加 resume
old = '  pause: (id: number) => client.post(`/projects/${id}/pause`),'
new = '''  pause: (id: number) => client.post(`/projects/${id}/pause`),
  resume: (id: number) => client.post(`/projects/${id}/resume`),'''

if "resume:" in src:
    print("\n[跳过] resume 已存在")
elif old in src:
    src = src.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(src)
    print("\n[OK] projectApi.resume 已添加")
else:
    print("\n[WARN] 锚点未匹配，当前 pause 行:")
    for l in src.split("\n"):
        if "pause" in l:
            print("  " + repr(l[:100]))

# 校验
print("\n校验:")
ts = open(p, encoding="utf-8").read()
print("  resume: defined =", "resume:" in ts)
