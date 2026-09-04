# -*- coding: utf-8 -*-
"""看 deliverables 的时间线 + experiments 目录（数据可能在这）"""
import os, datetime

ROOT = r"D:\111-1\AI_Scientist_v2\backend\output"
print("=== output/ 结构 ===")
for name in ["deliverables", "experiments", "pdf_reports"]:
    p = os.path.join(ROOT, name)
    if os.path.isdir(p):
        print(f"\n{name}/")
        for sub in sorted(os.listdir(p))[:25]:
            sp = os.path.join(p, sub)
            if os.path.isdir(sp):
                mtime = os.path.getmtime(sp)
                dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                n_files = sum(len(f) for _, _, f in os.walk(sp))
                print(f"  {sub:<20} {dt}  ({n_files} files)")

# experiments 里可能有 pipeline 运行记录（连 DB 的 project id）
print("\n=== experiments 子目录样本 ===")
exp = os.path.join(ROOT, "experiments")
if os.path.isdir(exp):
    for pid_dir in sorted(os.listdir(exp))[:5]:
        pp = os.path.join(exp, pid_dir)
        if os.path.isdir(pp):
            print(f"  {pid_dir}/")
            for f in sorted(os.listdir(pp))[:8]:
                print(f"    {f}")
