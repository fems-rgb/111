import asyncio, importlib.util, os, sys
ROOT=r"D:\111-1\AI_Scientist_v2\backend"
P=os.path.join(ROOT,"app","services","experiment_engine.py")
spec=importlib.util.spec_from_file_location("m",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

# 模拟 experiment_lab._exec: 前端传 data_table
async def t():
    data_table={"columns":["x","y"],"rows":[[1,100],[2,200],[3,300]]}
    res=await m.run_experiment(
        "print(\"DF:\", type(df).__name__)\nprint(\"SUM:\", df[\"y\"].sum())",
        902, 30, False, meta={"data_table": data_table})
    print(res.get("output_text","").strip()[-300:])
    print("data_table回写:", res.get("data_table") is not None)
asyncio.run(t())
