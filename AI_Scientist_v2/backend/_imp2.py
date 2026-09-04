P="app\services\experiment_engine.py"
lines=open(P,encoding="utf-8",errors="ignore").read().splitlines()
for i,l in enumerate(lines):
    s=l.strip()
    if s.startswith(("BUILTIN_TEMPLATES","TEMPLATES","BUILTIN","_TEMPLATES","OUTPUT_ROOT","ROOT_DIR")) or \
       "BUILTIN" in s or ("TEMPLATES" in s and ("=" in s or "list" in s or "dict" in s)):
        print(f"L{i+1}: {l}")
