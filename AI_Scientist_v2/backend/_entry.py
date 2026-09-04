import os, re
ROOT=r"D:\111-1\AI_Scientist_v2"
for rel in [r"backend\app\api\v1\experiment_lab.py", r"backend\app\agents\orchestrator.py"]:
    P=os.path.join(ROOT,rel)
    print("="*70); print(rel); print("="*70)
    lines=open(P,encoding="utf-8",errors="ignore").read().splitlines()
    # 找函数签名(含 run_experiment 调用所在函数)及 data_table/meta/request 相关
    for i,l in enumerate(lines):
        s=l.strip()
        if any(k in s for k in ["def ","data_table","meta","request","body","ExperimentRequest","pydantic","BaseModel","project.","run."]):
            print(f"  L{i+1}: {l}")
