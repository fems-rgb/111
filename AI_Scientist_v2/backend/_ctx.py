# -*- coding: utf-8 -*-
"""在 export.py 的上下文里，打印 L143 处 AgentTask.status 的真实枚举"""
import asyncio
from app.database.session import AsyncSessionLocal
from app.api.v1 import export as export_module   # ← 关键：走和报错同一个导入路径
from app.database.models import AgentTask as AgentTask_main

print("=== export 模块里的 AgentTask ===")
print("  export.AgentTask:", export_module.AgentTask)
print("  AgentTask(主):   ", AgentTask_main)
print("  是同一个?", export_module.AgentTask is AgentTask_main)

# export 里那个 AgentTask 的 status 枚举
col = export_module.AgentTask.__table__.c.status
print("\n=== export.AgentTask.status 枚举（报错那一刻的真实枚举）===")
print("  enum_class:", col.type.enum_class)
print("  成员:", [e.name for e in col.type.enum_class])
print("  值:", [e.value for e in col.type.enum_class])

# 对比 Project 里用的 status 枚举
print("\n=== Project.status 列枚举 ===")
pcol = export_module.Project.__table__.c.status
print("  enum_class:", pcol.type.enum_class)
print("  值:", [e.value for e in pcol.type.enum_class] if pcol.type.enum_class else "None(可能是String)")
