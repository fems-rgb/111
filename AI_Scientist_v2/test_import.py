import os, sys
out = []
def add(s=""): out.append(s)
sys.path.insert(0, os.path.abspath("backend"))

add("="*64); add("手动调用导入逻辑，观察是否真 commit"); add("="*64)

try:
    from app.data.science125 import SCIENCE_125_DATA
    add("[1] SCIENCE_125_DATA 条数: %d" % len(SCIENCE_125_DATA))
    add("     首条: %s" % str(SCIENCE_125_DATA[0])[:90])
except Exception as e:
    add("[1] 导入数据失败 %s: %s" % (type(e).__name__, e))

# 找导入函数
add(""); add("[2] 定位导入函数")
import importlib, pkgutil
found = []
for m in pkgutil.walk_packages(["backend.app"], prefix="backend.app."):
    if any(k in m.name for k in ("question", "science", "bank", "task")):
        found.append(m.name)
for n in found[:15]:
    try:
        mod = importlib.import_module(n)
        for a in dir(mod):
            if any(k in a.lower() for k in ("import", "science", "seed", "bulk", "create")):
                add("    %-40s -> %s" % (n, a))
    except Exception as e:
        add("    %-40s ERR %s" % (n, e))

add(""); add("[3] 导入按钮对应的 API 端点（后端路由）")
for n in found[:15]:
    try:
        import inspect
        mod = importlib.import_module(n)
        src = inspect.getsource(mod)
        for line in src.split("\n"):
            if "@" in line and any(k in line for k in ("post", "put", "import", "science")):
                add("    %s: %s" % (n.split(".")[-1], line.strip()[:110]))
    except Exception:
        pass

add(""); add("="*64)
open("test_import_out.txt","w",encoding="utf-8").write("\n".join(out))
print("\n".join(out))