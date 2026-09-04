import os, re
ROOT=r"D:\111-1\AI_Scientist_v2"
for rel in [r"backend\app\api\v1\experiment_lab.py", r"backend\app\agents\orchestrator.py"]:
    P=os.path.join(ROOT,rel)
    print("="*60)
    print(rel)
    print("="*60)
    lines=open(P,encoding="utf-8",errors="ignore").read().splitlines()
    for i,l in enumerate(lines):
        if "run_experiment(" in l:
            start=i
            # 打印该行及后续直到 ) 
            buf=[l]
            depth=l.count("(")-l.count(")")
            j=i+1
            while j<len(lines) and depth>0:
                buf.append(lines[j]); depth+=lines[j].count("(")-lines[j].count(")")
                j+=1
            for b in buf: print(f"  L{i+1+buf.index(b) if False else start+buf.index(b)+1}: {b}")
            # 打印上文 5 行(找 data_table/meta 来源)
            print("  --- 上文 ---")
            for k in range(max(0,start-8),start):
                print(f"  L{k+1}: {lines[k]}")
