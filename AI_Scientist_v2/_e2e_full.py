# -*- coding: utf-8 -*-
"""模拟：run_experiment 自动绘图 → 产出项目专属图 → PDF 能取到"""
import os, sys, asyncio, base64
ROOT = r"D:\111-1\AI_Scientist_v2\backend"
sys.path.insert(0, ROOT)

# 清理 project_1 旧图（模拟全新运行）
charts = os.path.join(ROOT, "output", "deliverables", "project_1", "charts")
if os.path.exists(charts):
    for f in list(os.listdir(charts)):
        os.remove(os.path.join(charts, f))

# 导入 run_experiment（空代码 → 触发自动绘图兜底）
from app.services.experiment_engine import run_experiment

# run_id 用 project_id，保证每个项目独特
run_id = 1
async def main():
    # code="" 触发"代码未产出图"分支 → 自动生成 3 张
    res = await run_experiment("", run_id, timeout=60, generate_video=False)
    print("[run_experiment] success=", res["success"], "charts=", len(res["charts"]))
    for c in res["charts"]:
        print("  图:", c["filename"], os.path.getsize(c["path"])//1024, "KB")
    return res

res = asyncio.run(main())

# 同时把图复制到 deliverables/project_1/charts/（模拟 stageC 回写路径）
os.makedirs(charts, exist_ok=True)
import shutil
for c in res["charts"]:
    dst = os.path.join(charts, c["filename"])
    shutil.copy(c["path"], dst)
print("\n[已复制] 到 deliverables/project_1/charts/:", sorted(os.listdir(charts)))

# 复刻 stageE 取图逻辑
project_id = 1
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
chart_files = [{"b64": base64.b64encode(open(p,"rb").read()).decode(),"filename":fn} for fn,p in sorted(_all.items())]
print("[PDF取图] 可嵌入图表数:", len(chart_files))
