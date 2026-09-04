import urllib.request, json
BASE = "http://localhost:8000/api/v1"
# 先拿 token（看你登录接口，这里假设有 /auth/login）
# 如果没有鉴权，直接调
try:
    req = urllib.request.urlopen(f"{BASE}/projects/1")
    print("GET /projects/1 ->", req.status, req.read().decode()[:300])
except Exception as e:
    print("GET /projects/1 失败:", e)

# 看 export 接口
for path in ["/projects/1/export/pdf", "/projects/1/resume"]:
    try:
        req = urllib.request.urlopen(f"{BASE}{path}")
        print(f"GET {path} ->", req.status, req.headers.get("content-type"))
    except Exception as e:
        print(f"GET {path} 失败:", str(e)[:200])
