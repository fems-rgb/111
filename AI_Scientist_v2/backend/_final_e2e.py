# -*- coding: utf-8 -*-
"""最终验证：从 backend/ 启动，模拟完整 stageC → PDF 取图"""
import os, sys, asyncio, shutil, glob
sys.path.insert(0, os.getcwd())
from app.services.experiment_engine import run_experiment, OUTPUT_ROOT

print("[验证] OUTPUT_ROOT =", OUTPUT_ROOT)
ROOT = os.getcwd()  # backend/

project_id = 1
run_id = 900001

# 清理
exp_dir = os.path.join(OUTPUT_ROOT, str(run_id), "charts")
if os.path.exists(exp_dir): shutil.rmtree(exp_dir)
deliv_dir = os.path.join(ROOT, "output", "deliverables", f"project_{project_id}", "charts")
os.makedirs(deliv_dir, exist_ok=True)
for old in glob.glob(os.path.join(deliv_dir, "*")): os.remove(old)

# 1. 模拟 stageC：run_experiment（空代码 → 自动绘图兜底）
async def main():
    return await run_experiment("", run_id, timeout=60, generate_video=False)
res = asyncio.run(main())
print("[stageC] charts=", len(res["charts"]))
assert os.path.isdir(exp_dir), "实验图目录未生成！"
print("[stageC] 图在:", exp_dir, os.listdir(exp_dir))

# 2. 模拟 stageC 同步逻辑（复刻 orchestrator 里的 SYNC 块）
_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(r"app\agents\orchestrator.py")))))
_deli_charts = os.path.join(_backend, "output", "deliverables", f"project_{project_id}", "charts")
os.makedirs(_deli_charts, exist_ok=True)
for old in glob.glob(os.path.join(_deli_charts, "*")): os.remove(old)
for fn in sorted(os.listdir(exp_dir)):
    if fn.lower().endswith((".png",".jpg",".svg")):
        shutil.copy(os.path.join(exp_dir, fn), os.path.join(_deli_charts, fn))
print("[同步] ->", _deli_charts, sorted(os.listdir(_deli_charts)))

# 3. 模拟 export.py stageE 取图（完全一致逻辑）
import base64
_PROJ_ROOT = _backend  # 就是 backend
_all = {}
for sub in ["deliverables"]:
    d = os.path.join(_PROJ_ROOT, "output", sub, f"project_{project_id}", "charts")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".png",".jpg",".svg")):
                _all[f] = os.path.join(d,f)
print("\n[PDF取图] 候选:", list(_all.keys()))
print("[PDF取图] 全部无占位:", all("rotation_curve" not in v for v in _all.values()))
chart_files = [{"b64": base64.b64encode(open(p,"rb").read()).decode(),"filename":fn} for fn,p in sorted(_all.items())]
print("[PDF取图] 可嵌入图表数:", len(chart_files), "(图文并茂 ✅)")
