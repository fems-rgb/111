# -*- coding: utf-8 -*-
"""验证：从 experiment_engine 导入 OUTPUT_ROOT，确保路径一致"""
import os, sys, asyncio, shutil, glob
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
sys.path.insert(0, ROOT)
from app.services.experiment_engine import run_experiment, OUTPUT_ROOT

print("[验证] OUTPUT_ROOT =", OUTPUT_ROOT)

project_id = 1
run_id = 900001

# 清理实验目录
exp_dir = os.path.join(OUTPUT_ROOT, str(run_id), "charts")
if os.path.exists(exp_dir):
    shutil.rmtree(exp_dir)

async def main():
    res = await run_experiment("", run_id, timeout=60, generate_video=False)
    print("[run_experiment] charts=", len(res["charts"]))
    for c in res["charts"]:
        print("  图:", c["filename"], "->", c["path"])
main_sync = asyncio.run(main())

# 确认 exp_dir 有图
print("\n[实验目录] exp_dir =", exp_dir)
print("[实验目录] 存在?", os.path.isdir(exp_dir), "内容:", os.listdir(exp_dir) if os.path.isdir(exp_dir) else "N/A")

# 同步到 deliverables
deliv_dir = os.path.join(ROOT, "output", "deliverables", f"project_{project_id}", "charts")
os.makedirs(deliv_dir, exist_ok=True)
# ① 清空
for old in glob.glob(os.path.join(deliv_dir, "*")):
    os.remove(old)
# ② 同步
if os.path.isdir(exp_dir):
    for fn in sorted(os.listdir(exp_dir)):
        if fn.lower().endswith((".png",".jpg",".svg")):
            shutil.copy(os.path.join(exp_dir, fn), os.path.join(deliv_dir, fn))

print("\n[同步后] deliverables/project_1/charts/:", sorted(os.listdir(deliv_dir)))
print("[验证] 无占位图残留:", "rotation_curve" not in "".join(os.listdir(deliv_dir)))

# PDF 取图逻辑
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py")))))
_all = {}
d = os.path.join(_PROJ_ROOT,"output","deliverables",f"project_{project_id}","charts")
if os.path.isdir(d):
    for f in sorted(os.listdir(d)):
        if f.lower().endswith((".png",".jpg",".svg")):
            _all[f] = os.path.join(d,f)
print("\n[PDF取图] 候选:", list(_all.keys()))
print("[PDF取图] 全部无占位:", all("rotation_curve" not in v for v in _all.values()))
