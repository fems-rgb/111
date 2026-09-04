P = r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
lines = open(P, encoding="utf-8", errors="ignore").read().splitlines()
# 找 _build_wrapper 函数
start = None
for i, l in enumerate(lines):
    if "def _build_wrapper" in l:
        start = i; break
print(f"=== _build_wrapper @ L{start+1} ===")
for i in range(start, min(start+120, len(lines))):
    print(f"L{i+1}: {lines[i]}")
    if i > start and lines[i].strip().startswith("def ") and i != start:
        break
