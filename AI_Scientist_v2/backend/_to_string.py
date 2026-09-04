# -*- coding: utf-8 -*-
"""把 AgentTask.status 从 SAEnum 改成 String（彻底绕过枚举）
DB 里已是字符串 completed/failed，改 String 完全兼容。
"""
import shutil, re
P = r"D:\111-1\AI_Scientist_v2\backend\app\database\models.py"
src = open(P, encoding="utf-8").read().split("\n")

# 找到 status = Column(SAEnum(...)...) 那一行（无论 validate_enum 有没有）
for i, l in enumerate(src):
    if l.strip().startswith("status = Column(SAEnum(") and "TaskStatus" in l:
        print(f"找到 L{i+1}: {l.strip()}")
        # 替换为 String
        indent = l[:len(l)-len(l.lstrip())]
        src[i] = f'{indent}status = Column(String(32), default=TaskStatus.PENDING.value, nullable=False)'
        print(f"替换为: {src[i].strip()}")
        break
else:
    print("ERROR: 没找到 SAEnum(TaskStatus) 行，请手动检查 models.py L128-140")

open(P, "w", encoding="utf-8").write("\n".join(src))
import py_compile
py_compile.compile(P, doraise=True)
print("[语法OK] 已备份在 .bak_val5")
