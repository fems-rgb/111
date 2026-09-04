# -*- coding: utf-8 -*-
"""fix_builtin.py - 在 experiment_engine.py 定义真实 BUILTIN_TEMPLATES, 修复启动 ImportError。
   每个模板代码都自行构造 df (不依赖前端 data_table), 与现有 run_experiment 兼容。
"""
import os, ast, shutil

P = os.path.join(r"D:\111-1\AI_Scientist_v2\backend", "app", "services", "experiment_engine.py")
src = open(P, encoding="utf-8", errors="ignore").read()
ast.parse(src)
shutil.copy(P, P + ".builtin_bak")

# 若已有(幂等), 跳过
import re
if re.search(r"^BUILTIN_TEMPLATES\s*=", src, re.MULTILINE):
    print("[ok] BUILTIN_TEMPLATES 已存在, 跳过")
else:
    # 在 OUTPUT_ROOT 定义之后插入(模块顶层常量区)
    lines = src.split("\n")
    insert_at = None
    for i, l in enumerate(lines):
        if l.strip().startswith("OUTPUT_ROOT"):
            # 找到该赋值结束(单行或多行), 在其后插入
            j = i
            depth = 0
            for k in range(i, min(i + 6, len(lines))):
                depth += lines[k].count("[") + lines[k].count("{")
                depth -= lines[k].count("]") + lines[k].count("}")
                if depth == 0:
                    j = k
                    break
            insert_at = j + 1
            break
    if insert_at is None:
        insert_at = len(lines)

    indent = "    "  # 模块顶层
    builtin_src = '''

# ============================================================================
# 内置实验模板 (启动时 seed 到 ExperimentTemplate 表)
# 每个模板: {name, description, code, category}
# 注意: code 必须自行构造 df (本文件 wrapper 不再预设 df), 保证开箱即用。
# ============================================================================
BUILTIN_TEMPLATES = [
    {
        "name": "鸢尾花数据探索 (pandas 基础)",
        "description": "用内置小数据集演示 DataFrame 创建、统计描述与散点图。",
        "category": "入门",
        "code": """import pandas as pd
import matplotlib.pyplot as plt

# 构造示例数据 (实际使用时可替换为真实数据加载)
df = pd.DataFrame({
    "sepal_length": [5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0, 4.4, 4.9,
                    5.4, 4.8, 4.8, 4.3, 5.8, 5.7, 5.4, 5.1, 5.7, 5.1],
    "sepal_width":  [3.5, 3.0, 3.2, 3.1, 3.6, 3.9, 3.4, 3.4, 2.9, 3.1,
                    3.7, 3.4, 3.0, 3.0, 4.0, 4.4, 3.9, 3.5, 3.8, 3.8],
    "petal_length": [1.4, 1.4, 1.3, 1.5, 1.4, 1.7, 1.4, 1.5, 1.4, 1.5,
                    1.5, 1.6, 1.4, 1.1, 1.2, 1.5, 1.3, 1.4, 1.7, 1.5],
    "species":      ["setosa"]*10 + ["versicolor"]*10,
})

print("=== 数据概览 ===")
print(df.head())
print("\\n=== 统计描述 ===")
print(df.describe())
print("\\n=== 按品种分组均值 ===")
print(df.groupby("species")[["sepal_length","sepal_width","petal_length"]].mean())

# 散点图
fig, ax = plt.subplots(figsize=(6, 4))
colors = {"setosa": "red", "versicolor": "blue"}
for sp, sub in df.groupby("species"):
    ax.scatter(sub["sepal_length"], sub["sepal_width"], label=sp, c=colors.get(sp))
ax.set_xlabel("sepal_length"); ax.set_ylabel("sepal_width"); ax.legend()
fig.savefig("charts/scatter.png", dpi=100, bbox_inches="tight")
print("\\n[ok] 散点图已保存 -> charts/scatter.png")
""",
    },
    {
        "name": "正态分布随机数分析",
        "description": "用 numpy 生成随机数据, 绘制直方图与均值检验。",
        "category": "统计",
        "code": """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(42)
data = np.random.normal(loc=50, scale=10, size=500)
df = pd.DataFrame({"value": data})

print("=== 基本统计 ===")
print(f"样本数: {len(df)}")
print(f"均值:   {df['value'].mean():.3f}")
print(f"标准差: {df['value'].std():.3f}")
print(f"中位数: {df['value'].median():.3f}")

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(df["value"], bins=30, density=True, alpha=0.7, color="steelblue")
ax.axvline(df["value"].mean(), color="red", linestyle="--", label="均值")
ax.set_xlabel("value"); ax.set_ylabel("密度"); ax.legend()
fig.savefig("charts/hist.png", dpi=100, bbox_inches="tight")
print("[ok] 直方图已保存 -> charts/hist.png")
""",
    },
    {
        "name": "简单线性回归 (最小二乘)",
        "description": "构造带噪声的线性数据, 用 numpy 拟合直线并可视化。",
        "category": "建模",
        "code": """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(0)
x = np.linspace(0, 10, 50)
y = 2.5 * x + 1.0 + np.random.normal(0, 2.0, size=50)
df = pd.DataFrame({"x": x, "y": y})

# 最小二乘: y = a*x + b
n = len(df)
a = (n*(df["x"]*df["y"]).sum() - df["x"].sum()*df["y"].sum()) / \\
    (n*(df["x"]**2).sum() - (df["x"].sum())**2)
b = df["y"].mean() - a*df["x"].mean()
df["y_pred"] = a*df["x"] + b

print(f"拟合结果: y = {a:.4f}*x + {b:.4f}")
print(f"(真实:   y = 2.5000*x + 1.0000)")

fig, ax = plt.subplots(figsize=(7, 4))
ax.scatter(df["x"], df["y"], s=20, alpha=0.6, label="观测")
ax.plot(df["x"], df["y_pred"], color="red", label="拟合直线")
ax.set_xlabel("x"); ax.set_ylabel("y"); ax.legend()
fig.savefig("charts/regression.png", dpi=100, bbox_inches="tight")
print("[ok] 回归图已保存 -> charts/regression.png")
""",
    },
    {
        "name": "时间序列趋势分析",
        "description": "用日期索引 DataFrame 演示移动平均与趋势可视化。",
        "category": "入门",
        "code": """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 构造 90 天时间序列
dates = pd.date_range("2024-01-01", periods=90, freq="D")
trend = np.linspace(100, 160, 90)
noise = np.random.normal(0, 5, 90)
df = pd.DataFrame({"date": dates, "value": trend + noise}).set_index("date")
df["ma7"] = df["value"].rolling(7, center=True).mean()

print("=== 最近 10 天 ===")
print(df.tail(10).to_string())

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(df.index, df["value"], alpha=0.5, label="原始")
ax.plot(df.index, df["ma7"], color="red", linewidth=2, label="7日移动平均")
ax.set_xlabel("日期"); ax.set_ylabel("value"); ax.legend()
fig.autofmt_xdate()
fig.savefig("charts/timeseries.png", dpi=100, bbox_inches="tight")
print("[ok] 时间序列图已保存 -> charts/timeseries.png")
""",
    },
]


def _seed_builtin_templates_compat(db):
    """兼容: 若调用方期望 experiment_engine.seed_builtin_templates, 走 DB 版本。
    实际种子逻辑在 app.api.v1.experiment_lab.seed_builtin_templates (用 BUILTIN_TEMPLATES)。
    """
    from sqlalchemy import select, func, delete
    from app.database.models import ExperimentTemplate
    existing = (db.execute(select(func.count()).select_from(ExperimentTemplate).where(
        ExperimentTemplate.is_builtin == True)).scalar() or 0)
    if existing >= len(BUILTIN_TEMPLATES):
        return
    db.execute(delete(ExperimentTemplate).where(ExperimentTemplate.is_builtin == True))
    for t in BUILTIN_TEMPLATES:
        db.add(ExperimentTemplate(
            name=t["name"], description=t["description"],
            code=t["code"], category=t.get("category", "通用"), is_builtin=True))
    db.commit()
'''

    # 插入
    new_lines = lines[:insert_at] + builtin_src.split("\n") + lines[insert_at:]
    new_src = "\n".join(new_lines) + "\n"
    ast.parse(new_src)
    open(P, "w", encoding="utf-8", newline="\n").write(new_src)
    print(f"[ok] 定义 BUILTIN_TEMPLATES (4 个内置模板) @ 约 L{insert_at+1}")

# 校验
final = open(P, encoding="utf-8").read()
ast.parse(final)
print("\n=== 校验 ===")
import importlib.util
spec = importlib.util.spec_from_file_location("m", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
bt = getattr(m, "BUILTIN_TEMPLATES", None)
print("BUILTIN_TEMPLATES 可导入:", bt is not None)
print("  数量:", len(bt) if bt else 0)
if bt:
    for t in bt:
        print(f"    - {t['name']} ({t['category']})")
print("OUTPUT_ROOT 存在:", hasattr(m, "OUTPUT_ROOT"))
print("run_experiment 存在:", hasattr(m, "run_experiment"))
