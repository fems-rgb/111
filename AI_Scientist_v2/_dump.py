# -*- coding: utf-8 -*-
"""读取 project 表里「领域相关」字段的真实内容，定位硬编码/无关文字来源"""
import sqlite3

DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

cols = ["id", "title", "description", "research_question", "problem_statement", "rationale",
        "technical_details", "datasets", "paper_title", "paper_abstract", "methods",
        "experiments", "results", "hypotheses", "literature_refs"]
print("="*70)
print("projects 表字段列表")
print("="*70)
existing = [r["name"] for r in c.execute("PRAGMA table_info(projects)").fetchall()]
missing = [col for col in cols if col not in existing]
print("  缺失字段:", missing if missing else "无")

print()
print("="*70)
print("project 1 各领域字段（前 400 字）")
print("="*70)
row = c.execute("SELECT * FROM projects WHERE id=1").fetchone()
if not row:
    print("  project 1 不存在，尝试最新一条")
    row = c.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 1").fetchone()

for col in cols:
    if col not in existing:
        continue
    val = row[col]
    if val is None or str(val).strip() in ("", "[]", "{}"):
        print(f"\n  [{col}] = (空)")
        continue
    txt = str(val).replace("\n", " ")[:400]
    print(f"\n  [{col}] ({len(str(val))} 字)\n    {txt}")

c.close()
