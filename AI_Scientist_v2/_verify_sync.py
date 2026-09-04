# -*- coding: utf-8 -*-
"""验证：模拟 stageC 同步，确认 deliverables/project_1/charts/ 干净且只有真图"""
import os, sys, asyncio, shutil
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
sys.path.insert(0, ROOT)
from app.services.experiment_engine import run_experiment

project_id = 1
run_id = 900001

# 清理实验目录旧图，确保干净
exp_dir = os.path.join(ROOT, "output", "experiments", str(run_id), "charts")
if os.path.exists(exp_dir):
    shutil.rmtree(exp_dir)

async def main():
    res = await run_experiment("", run_id, timeout=60, generate_video=False)
    print("[run_experiment] charts=", len(res["charts"]))
    return res
asyncio.run(main())

# === 复刻 _fix_sync2 的同步逻辑 ===
deliv_dir = os.path.join(ROOT, "output", "deliverables", f"project_{project_id}", "charts")
os.makedirs(deliv_dir, exist_ok=True)
# ① 先清空旧图
import glob
for old in glob.glob(os.path.join(deliv_dir, "*")):
    os.remove(old)
# ② 再同步
if os.path.isdir(exp_dir):
    for fn in sorted(os.listdir(exp_dir)):
        if fn.lower().endswith((".png",".jpg",".svg")):
            shutil.copy(os.path.join(exp_dir, fn), os.path.join(deliv_dir, fn))

print("[同步后] deliverables/project_1/charts/:", sorted(os.listdir(deliv_dir)))
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
