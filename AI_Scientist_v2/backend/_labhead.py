P="app\api\v1\experiment_lab.py"
lines=open(P,encoding="utf-8",errors="ignore").read().splitlines()
for i,l in enumerate(lines):
    if i<30 or "BUILTIN" in l or "TEMPLATES" in l or "seed_builtin" in l:
        print(f"L{i+1}: {l}")
