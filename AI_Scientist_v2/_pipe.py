import os, re
print("="*64)
print("流水线执行/取消相关（orchestrator / pipeline）")
print("="*64)
for root, dirs, files in os.walk("backend/app"):
    for fn in files:
        if not fn.endswith(".py"):
            continue
        if "test" in fn or "mock" in fn:
            continue
        fp = os.path.join(root, fn)
        t = open(fp, encoding="utf-8", errors="ignore").read()
        if any(k in t for k in ["cancel", "abort", "pause", "stop", "shutdown"]) and any(k in t for k in ["asyncio.Task", "create_task", "CancelledError", "task.cancel"]):
            hits = []
            for i, l in enumerate(t.split("\n"), 1):
                if re.search(r"cancel|abort|pause|stop|CancelledError|create_task", l, re.I):
                    hits.append((i, l.strip()[:100]))
            if hits:
                print("\n%s" % fp.replace("backend/",""))
                for i, h in hits[:20]:
                    print("  L%d| %s" % (i, h))
