# -*- coding: utf-8 -*-
"""在真正出错的上下文里，打印 AgentTask.status 枚举的真实成员"""
import asyncio
from app.database.session import AsyncSessionLocal
from app.database.models import AgentTask, TaskStatus

# 关键：看运行时 AgentTask.status 列绑定的枚举到底是什么
col = AgentTask.__table__.c.status
print("=== AgentTask.status 列（从表元数据）===")
print("  type:", type(col.type).__name__)
print("  enum_class:", col.type.enum_class)
print("  实际成员:", [e.name for e in col.type.enum_class])
print("  实际值:", [e.value for e in col.type.enum_class])

print("\n=== 对比 TaskStatus 类 ===")
print("  成员:", list(TaskStatus.__members__.keys()))
print("  值:", [e.value for e in TaskStatus])

print("\n是否为同一个类:", col.type.enum_class is TaskStatus)
