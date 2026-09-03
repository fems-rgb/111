# ── 2) orchestrator 里"继续/启动"相关的关键函数签名 ──
lines = open("backend/app/agents/orchestrator.py", encoding="utf-8").read().split("\n")
print("="*64)
print("orchestrator.py 顶层函数定义")
print("="*64)
for i, l in enumerate(lines):
    s = l.strip()
    if s.startswith(("def ", "async def ")) and not s.startswith("def _"):
        print("%4d| %s" % (i+1, s[:110]))
