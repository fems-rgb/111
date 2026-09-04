# -*- coding: utf-8 -*-
"""看 AgentTask.status 列【真实类型】和 validate_enum 是否生效"""
from app.database.models import AgentTask, TaskStatus
import sqlalchemy as sa

col = AgentTask.__table__.c.status
print("Python type:", type(col.type))
print("full repr :", repr(col.type))
print("validate_enum attr:", getattr(col.type, "validate_enum", "MISSING"))
print("enum_class __name__:", col.type.enum_class.__name__)
print("enum_class id:", id(col.type.enum_class))
print("TaskStatus id:", id(TaskStatus))
print("同一个类?", col.type.enum_class is TaskStatus)

# 关键：这个 Enum 是 sqlalchemy.Enum 还是原生 enum？
print("\nisinstance sqlalchemy.Enum:", isinstance(col.type, sa.Enum))
print("type MRO:", [c.__name__ for c in type(col.type).__mro__])
