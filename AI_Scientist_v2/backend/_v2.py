
import importlib.util, asyncio, sys
P=r"D:\111-1\AI_Scientist_v2\backend\app\services\experiment_engine.py"
spec=importlib.util.spec_from_file_location("cem",P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
async def t():
    res=await m.run_experiment(
        "print(\"DF:\", type(df).__name__)\nprint(\"VAL:\", df[\"y\"].sum() if df is not None else 'NONE')",
        555, 30, False, {"data_table":{"columns":["x","y"],"rows":[[1,10],[2,20],[3,30]]}})
    print(res.get("output_text","").strip()[-400:])
asyncio.run(t())
