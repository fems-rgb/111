# -*- coding: utf-8 -*-
import shutil
P = r"D:\111-1\AI_Scientist_v2\backend\app\agents\writing.py"
shutil.copy(P, P + ".bak_visual2")
lines = open(P, encoding="utf-8").read().split("\n")

OLD = "- 结果可视化描述（图表内容说明，即使无法嵌入图片也要详细描述）"
NEW = """- 【必做·可视化代码】针对核心假设(H1-H5)，输出至少 3 个独立可执行的 Python 绘图代码块（用 ```python ... ``` 围栏）：
    · 代码块①「假设检验结果图」→ 保存为 假设检验图.png（回归系数/显著性/p值）
    · 代码块②「关键变量分布或相关性图」→ 保存为 变量分布.png 或 correlation.png
    · 代码块③「参数收敛或稳健性图」→ 保存为 收敛曲线.png
  · 代码自包含（import 齐全）；数据优先用 ExperimentRun 真实结果，否则用 numpy 模拟（固定 np.random.seed）
  · 每段必须以 `plt.savefig('图名.png', dpi=150, bbox_inches='tight')` 结尾
  · 三个 savefig 图名必须严格为：假设检验图.png / 变量分布.png / 收敛曲线.png
- 【保留】结果可视化描述文字（图文并茂说明每张图含义）"""

assert any(OLD in l for l in lines), "L142 未匹配"
for i, l in enumerate(lines):
    if OLD in l:
        indent = l[:len(l)-len(l.lstrip())]
        lines[i] = "\n".join(indent + x if x.strip() else x for x in NEW.split("\n"))
        break
open(P, "w", encoding="utf-8").write("\n".join(lines))
print("[已修改] writing.py L142: 增加可视化代码要求")

import py_compile
try: py_compile.compile(P, doraise=True); print("[语法OK]")
except Exception as e: print("[语法错误]", e)
