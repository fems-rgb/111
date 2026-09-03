import os, re

print("="*64)
print("[1] 前端：暂停/停止 按钮绑定的事件和方法")
print("="*64)
for root, dirs, files in os.walk("frontend/src"):
    for fn in files:
        if not fn.endswith((".ts", ".js", ".vue")):
            continue
        fp = os.path.join(root, fn)
        t = open(fp, encoding="utf-8", errors="ignore").read()
        if re.search(r"暂停|停止|pause|stop|abort|cancel", t, re.I):
            for i, l in enumerate(t.split("\n"), 1):
                s = l.strip()
                if re.search(r"暂停|停止|pause|stop|abort|cancel", s, re.I) and (
                    "click" in s.lower() or "@click" in s or "axios" in s or "client" in s
                    or "fetch" in s or "async" in s or "function" in s or "=>" in s
                    or s.startswith("const") or s.startswith("this.")
                ):
                    print("%s L%d| %s" % (fp.replace("frontend/",""), i, s[:110]))

print()
print("="*64)
print("[2] 后端：pause/stop/abort/cancel 接口")
print("="*64)
for root, dirs, files in os.walk("backend/app/api"):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        fp = os.path.join(root, fn)
        t = open(fp, encoding="utf-8", errors="ignore").read()
        if re.search(r"pause|stop|abort|cancel|暂停|停止", t, re.I):
            for i, l in enumerate(t.split("\n"), 1):
                s = l.strip()
                if ("@router" in s and "pause" in s.lower()) or ("@router" in s and "stop" in s.lower()) or ("@router" in s and "abort" in s.lower()) or ("@router" in s and "cancel" in s.lower()):
                    print("%s L%d| %s" % (fp.replace("backend/",""), i, s[:110]))
            # 也找函数定义
            for m in re.finditer(r"async def (pause|stop|abort|cancel|_pause|_stop)[^\n]*", t, re.I):
                print("%s L%d| %s" % (fp.replace("backend/",""), t[:m.start()].count("\n")+1, m.group(0)[:110]))
