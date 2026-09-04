# -*- coding: utf-8 -*-
P = "app/api/v1/experiment_lab.py"
lines = open(P, encoding="utf-8", errors="ignore").read().splitlines()
for i, l in enumerate(lines[:40]):
    print(f"L{i+1}: {l}")
