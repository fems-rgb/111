# -*- coding: utf-8 -*-
"""验证：模拟 stageC 完整流程，确认图最终落到 deliverables/project_{pid}/charts/"""
import os, sys, asyncio, shutil
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
sys.path.insert(0, ROOT)

from app.services.experiment_engine import run_experiment

project_id = 1
# 模拟：ExperimentRun.id 是自增（如 900001），但我们要图落到 project_1
run_id = 900001   # 真实的 ExperimentRun.id

async def main():
    # 空代码 → 触发自动绘图兜底
    res = await run_experiment("", run_id, timeout=60, generate_video=False)
    print("[run_experiment] success=", res["success"], "charts=", len(res["charts"]))
    for c in res["charts"]:
        print("  图:", c["filename"], "->", c["path"])
    return res

res = asyncio.run(main())

# === 关键：把 experiments/{run_id}/charts/ 同步到 deliverables/project_{project_id}/charts/ ===
exp_dir = os.path.join(ROOT, "output", "experiments", str(run_id), "charts")
deliv_dir = os.path.join(ROOT, "output", "deliverables", f"project_{project_id}", "charts")
os.makedirs(deliv_dir, exist_ok=True)
# 清理旧的 rotation_curve 占位
for f in ["rotation_curve.png"]:
    fp = os.path.join(deliv_dir, f)
    if os.path.exists(fp): os.remove(fp)

if os.path.isdir(exp_dir):
    for f in os.listdir(exp_dir):
        if f.lower().endswith((".png",".jpg",".svg")):
            shutil.copy(os.path.join(exp_dir, f), os.path.join(deliv_dir, f))
print("\n[同步] experiments/%s/charts/ -> deliverables/project_%s/charts/" % (run_id, project_id))
print("[结果]", sorted(os.listdir(deliv_dir)))

# 验证 PDF 取图逻辑
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py")))))
_cands = [os.path.join(_PROJ_ROOT,"output","deliverables",f"project_{project_id}","charts")]
_all = {}
for d in _cands:
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".png",".jpg",".svg")):
                _all[f] = os.path.join(d,f)
print("\n[PDF取图] 候选:", list(_all.keys()))
print("[PDF取图] 全部无占位:", all("rotation_curve" not in v for v in _all.values()))
