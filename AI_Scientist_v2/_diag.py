print("="*64)
print("[1] 后端是否在跑（检查端口 8000）")
print("="*64)
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    r = s.connect_ex(("localhost", 8000))
    print("  8000 端口:", "开放" if r == 0 else "未开放/被占用")
    s.close()
except Exception as e:
    print("  检查失败:", e)

print()
print("="*64)
print("[2] resume 路由是否注册（检查 API 前缀）")
print("="*64)
lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
for i, l in enumerate(lines[:20]):
    print("  L%d| %s" % (i+1, l.rstrip()[:120]))

# 检查 main.py 里路由前缀
print()
print("="*64)
print("[3] main.py 路由挂载（api_prefix）")
print("="*64)
main_lines = open("backend/app/main.py", encoding="utf-8").read().split("\n")
for l in main_lines:
    if "include_router" in l or "prefix" in l.lower() or "API" in l:
        print("  " + l.strip()[:120])

print()
print("="*64)
print("[4] resume 接口完整代码 + 状态校验")
print("="*64)
proj_lines = open("backend/app/api/v1/projects.py", encoding="utf-8").read().split("\n")
in_resume = False
for i, l in enumerate(proj_lines):
    if "@router.post(\"/{project_id}/resume\")" in l:
        in_resume = True
    if in_resume:
        print("  L%d| %s" % (i+1, l.rstrip()[:130]))
        if i > 0 and l.strip().startswith("def ") and in_resume and i > 5:
            break
