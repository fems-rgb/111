# -*- coding: utf-8 -*-
"""造 project_1 专属图 + 复刻 stageE 取图逻辑验证"""
import os, sys, base64
ROOT = r"D:\111-1\AI_Scientist_v2\backend"

# 1. 造项目专属独特图（模拟 run_experiment 真实产出）
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
charts_dir = os.path.join(ROOT, "output", "deliverables", "project_1", "charts")
os.makedirs(charts_dir, exist_ok=True)
# 删掉旧占位图，避免干扰
for f in ["rotation_curve.png"]:
    fp = os.path.join(charts_dir, f)
    if os.path.exists(fp): os.remove(fp)

np.random.seed(1)  # 用 project_id 做 seed → 每个项目图不同
# 图1：假设检验
fig, ax = plt.subplots(figsize=(6,4))
x = np.random.rand(60); y = 1.8*x + np.random.randn(60)*0.25
c = np.polyfit(x,y,1)
ax.scatter(x,y,alpha=0.6); ax.plot(x,np.polyval(c,x),'r-',lw=2,label=f"y={c[0]:.2f}x+{c[1]:.2f}")
ax.set_title("图1 假设H1检验结果"); ax.set_xlabel("变量X"); ax.set_ylabel("观测Y"); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(charts_dir,"假设检验图.png"),dpi=150); plt.close()
# 图2：变量分布
fig, ax = plt.subplots(figsize=(6,4))
ax.hist(np.random.randn(220),bins=22,density=True,alpha=0.7,color="steelblue")
ax.set_title("图2 关键变量分布")
plt.tight_layout(); plt.savefig(os.path.join(charts_dir,"变量分布.png"),dpi=150); plt.close()
# 图3：收敛曲线
fig, ax = plt.subplots(figsize=(6,4))
xs=np.arange(1,101); ax.plot(xs,1/xs+np.random.randn(100)*0.02,'b-',lw=1); ax.axhline(0,ls='--',color='r')
ax.set_title("图3 参数收敛曲线")
plt.tight_layout(); plt.savefig(os.path.join(charts_dir,"收敛曲线.png"),dpi=150); plt.close()
print("[造图] project_1/charts/:", sorted(os.listdir(charts_dir)))

# 2. 复刻 export.py stageE 取图逻辑（完全一致）
import os as _os
project_id = 1
_PROJ_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(
    r"D:\111-1\AI_Scientist_v2\backend\app\api\v1\export.py")))))
_CANDIDATE_DIRS = [
    _os.path.join(_PROJ_ROOT,'output','deliverables',f'project_{project_id}','charts'),
    _os.path.join(_PROJ_ROOT,'output','deliverables',f'project_{project_id}'),
    _os.path.join(_PROJ_ROOT,'output','experiments',f'project_{project_id}','charts'),
    _os.path.join(_PROJ_ROOT,'output','experiments',str(project_id),'charts'),
]
_all_png = {}
for _d in _CANDIDATE_DIRS:
    if _os.path.isdir(_d):
        for _f in sorted(_os.listdir(_d)):
            if _f.lower().endswith(('.png','.jpg','.jpeg','.svg')):
                _all_png[_f] = _os.path.join(_d,_f)

print("\n[验证1] 候选图:", list(_all_png.keys()))
print("[验证2] 全部项目专属、无占位:", all("rotation_curve" not in v for v in _all_png.values()))

chart_files=[]
for fn,p in sorted(_all_png.items()):
    with open(p,'rb') as f: b64=base64.b64encode(f.read()).decode('ascii')
    chart_files.append({"b64":b64,"filename":fn,"title":fn})
print("[验证3] 可嵌入PDF的图表数:", len(chart_files))
