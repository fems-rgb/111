# -*- coding: utf-8 -*-
"""fix_seaborn.py - 在 wrapper 里自动注入 data=df, 让 sns.xxxplot(x=col, y=col) 不传 data 也能跑。
   修改 _build_wrapper: 
   1) import seaborn + 定义补丁函数
   2) 在 _ns 里预置 sns (已打补丁)
"""
import os, ast, shutil

ENG = os.path.join(r"D:\111-1\AI_Scientist_v2\backend", "app", "services", "experiment_engine.py")
src = open(ENG, encoding="utf-8", errors="ignore").read()
ast.parse(src)
shutil.copy(ENG, ENG + ".seaborn_bak")

lines = src.split("\n")

# ---- 定位 L213 "wrapper = (" 之后的 import 块 ----
# 在 "import matplotlib.animation as animation" 之后插入 seaborn 补丁定义
# 找 animation import 行
anim_line = None
for i, l in enumerate(lines):
    if "import matplotlib.animation as animation" in l:
        anim_line = i
        break
assert anim_line is not None, "找不到 animation import"

# 在 anim_line 后插入 seaborn 补丁定义 (在 wrapper 字符串内部)
indent = "        "  # wrapper 字符串的缩进
patch_def = [
    indent + "import seaborn as sns",
    indent + "import functools as _functools",
    indent + "",
    indent + "# === [fix-seaborn] 自动注入 data=df ===",
    indent + "def _patch_sns(__df):",
    indent + "    if __df is None:",
    indent + "        return sns",
    indent + "    _COLS = list(__df.columns) if hasattr(__df, 'columns') else []",
    indent + "    _PLOTTERS = ['scatterplot','lineplot','barplot','boxplot','violinplot',",
    indent + "                 'stripplot','swarmplot','pointplot','countplot','catplot',",
    indent + "                 'lmplot','regplot','residplot','displot','relplot',",
    indent + "                 'kdeplot','histplot','ecdfplot','rugplot','pairplot',",
    indent + "                 'jointplot','heatmap']",
    indent + "    def _make(name):",
    indent + "        orig = getattr(sns, name)",
    indent + "        if not callable(orig): return orig",
    indent + "        @_functools.wraps(orig)",
    indent + "        def _p(*a, **kw):",
    indent + "            if kw.get('data') is None:",
    indent + "                xs = [kw.get(k) for k in ('x','y','hue','size','style') if kw.get(k) is not None]",
    indent + "                if any(isinstance(v,str) and v in _COLS for v in xs):",
    indent + "                    kw['data'] = __df",
    indent + "            return orig(*a, **kw)",
    indent + "        return _p",
    indent + "    for _n in _PLOTTERS:",
    indent + "        if hasattr(sns, _n):",
    indent + "            setattr(sns, _n, _make(_n))",
    indent + "    return sns",
    indent + "",
]
lines = lines[:anim_line+1] + patch_def + lines[anim_line+1:]

# ---- 定位 _ns 构造 (L273-274), 把 sns 加进去 ----
src2 = "\n".join(lines)
idx = src2.find("    _ns = {'__builtins__': builtins, 'df': df,")
assert idx != -1, "找不到 _ns 构造"
# 找到这行的结尾
line_start = src2.rfind("\n", 0, idx) + 1
line_end = src2.find("\n", idx)
ns_line = src2[line_start:line_end]
# 替换为加入 'sns': _patch_sns(df)
new_ns = "    _ns = {'__builtins__': builtins, 'df': df, 'sns': _patch_sns(df),\n           'pd': pd, 'np': np, 'plt': plt, 'os': os, 'json': json}"
src2 = src2[:line_start] + new_ns + src2[line_end:]

# 校验
ast.parse(src2)
open(ENG, "w", encoding="utf-8", newline="\n").write(src2)
final = open(ENG, encoding="utf-8").read()
ast.parse(final)

print("[ok] seaborn 补丁已注入 wrapper")
print("\n=== 验证: 关键片段 ===")
# 重新读, 显示 _ns 行 + patch 定义开头
for i, l in enumerate(final.splitlines()):
    if "_patch_sns" in l or "'sns':" in l or "def _patch_sns" in l:
        print(f"  L{i+1}: {l}")
