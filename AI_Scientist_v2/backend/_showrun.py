p=r"output\experiments\89\_run.py"
lines=open(p,encoding="utf-8",errors="ignore").read().splitlines()
for i,l in enumerate(lines):
    if i < 15:
        print(f"L{i+1}: {l}")
