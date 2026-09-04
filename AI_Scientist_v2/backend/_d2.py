P = r"app\services\experiment_engine.py"
lines = open(P, encoding="utf-8").read().splitlines()
print("总行数:", len(lines))
for i,l in enumerate(lines):
    s=l.strip()
    if s.startswith("def _auto_generate_charts") or 'exec("""' in l or '"exec(' in l or "def _build_wrapper" in s or "_make_df" in s:
        print(f"L{i+1}: {s[:120]}")
