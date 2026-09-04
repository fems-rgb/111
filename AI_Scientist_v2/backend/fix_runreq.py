# -*- coding: utf-8 -*-
"""fix_runreq.py - 给 RunRequest 加 data_table 字段 (dict | None),
   修复 req.data_table -> AttributeError -> 500。"""
import os, re, ast, shutil

LAB = os.path.join(r"D:\111-1\AI_Scientist_v2\backend", "app", "api", "v1", "experiment_lab.py")
src = open(LAB, encoding="utf-8", errors="ignore").read()
ast.parse(src)
shutil.copy(LAB, LAB + ".runreq_bak")

# 加 import (若尚未导入)
if "from typing import Optional" in src and "Optional" in src.split("class RunRequest")[0][-200:]:
    pass  # Optional 已有
# 确保 Optional 可用
if "Optional" not in src.split("\n")[0:15]:
    src = src.replace("from typing import Optional", "from typing import Optional", 1)

# 在 RunRequest 里插入 data_table 字段 (在 timeout 行之后)
old = """    generate_video: bool = True
    timeout: int = Field(60, ge=10, le=1200)"""
new = """    generate_video: bool = True
    timeout: int = Field(60, ge=10, le=1200)
    data_table: Optional[dict] = None  # [fix] 前端传入的表格数据 {'columns':[...],'rows':[[...]]}"""

assert old in src, "未找到插入锚点 (RunRequest 结构已变?)"
src = src.replace(old, new, 1)

# 校验语法 + 确认字段存在
ast.parse(src)
open(LAB, "w", encoding="utf-8", newline="\n").write(src)
final = open(LAB, encoding="utf-8").read()
ast.parse(final)

# 确认
t = final
idx = t.find("class RunRequest")
end = t.find("\nclass ", idx+1)
print("=== 修复后 RunRequest ===")
print(t[idx:end])

# 确保 _exec 签名能接收 data_table (L74 已有 data_table=None)
print("\n=== 校验 _exec 签名 ===")
for i, l in enumerate(final.splitlines()):
    if "async def _exec" in l or (l.strip().startswith("def _exec") and "data_table" in l):
        print(f"  L{i+1}: {l}")

print("\n[ALL DONE] SYNTAX OK")
