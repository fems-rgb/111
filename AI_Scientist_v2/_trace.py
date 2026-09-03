# -*- coding: utf-8 -*-
"""追踪 export.py 产物(writing/analysis)的存储位置，以及 challenge_cup_pdf 的真实数据来源"""
import sqlite3

DB = r"D:\111-1\AI_Scientist_v2\backend\zhixing.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row

# 1) 看 documents 表结构（很可能是 writing 的归宿）
print("="*70)
print("[1] documents 表（最可能存 writing/PDF 产物）")
print("="*70)
cols = [r["name"] for r in c.execute("PRAGMA table_info(documents)")]
print("  列:", cols)
row = c.execute("SELECT * FROM documents ORDER BY id DESC LIMIT 1").fetchone()
if row:
    d = dict(row)
    print("  最新一行字段:")
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 120:
            print(f"    {k}: ({len(v)}字) {v[:120]}...")
        else:
            print(f"    {k}: {v}")

# 2) projects.final_output / config / metadata 里有没有 writing
print()
print("="*70)
print("[2] projects 的 final_output / config / metadata 样例")
print("="*70)
row = c.execute("SELECT id, title, research_question, final_output, config, metadata FROM projects ORDER BY id DESC LIMIT 1").fetchone()
if row:
    for k in ["id","title","research_question","final_output","config","metadata"]:
        v = row[k]
        s = str(v or "")
        print(f"  {k}: ({len(s)}字) {s[:150]}{'...' if len(s)>150 else ''}")

# 3) hypotheses 表样例（确认 H1-H5 的真实 statement）
print()
print("="*70)
print("[3] hypotheses 表样例（H1-H5 真实内容）")
print("="*70)
for r in c.execute("SELECT * FROM hypotheses ORDER BY id DESC LIMIT 6"):
    d = dict(r)
    print(f"  id={d.get('id')} hypo_id={d.get('hypo_id')}")
    print(f"    statement: {(d.get('statement') or '')[:120]}")
    print(f"    variables: {(str(d.get('variables')) or '')[:80]}")

# 4) challenge_cup_pdf 上下文到底取到了啥
print()
print("="*70)
print("[4] challenge_cup_pdf.py 里 project 字段的实际值（用 sqlite 模拟）")
print("="*70)
row = c.execute("SELECT * FROM projects ORDER BY id DESC LIMIT 1").fetchone()
proj = dict(row)
for f in ["methods","rationale","paper_title","paper_abstract","experiments","results","hypotheses","datasets"]:
    print(f"  project.{f} = {repr(getattr(type('',(),{f:'?'})(), f))}  <- 字段是否存在?")

c.close()
