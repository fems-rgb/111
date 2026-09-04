# -*- coding: utf-8 -*-
P = "app/services/experiment_engine.py"
text = open(P, encoding="utf-8", errors="ignore").read()
lines = text.splitlines()
print("===== A) experiment_engine.py 中所有 TEMPLATE / BUILTIN / 列表/字典定义 =====")
for i, l in enumerate(lines):
    s = l.strip()
    low = s.lower()
    if ("template" in low) or ("builtin" in low) or s.startswith("SEED") or s.startswith("CODES"):
        print(f"L{i+1}: {l}")
print()
print("===== B) 所有全大写顶层赋值 (可能放模板的容器) =====")
import re
for i, l in enumerate(lines[:120]):
    if re.match(r"^[A-Z][A-Z0-9_]+\s*=\s*(\[|\{)", l):
        print(f"L{i+1}: {l}")
