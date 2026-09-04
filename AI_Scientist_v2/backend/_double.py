# -*- coding: utf-8 -*-
"""验证：TaskStatus 是否被定义了两次（两个不同 id）"""
import app.database.models as M
from app.database.models import TaskStatus

# 直接读磁盘，看有几处 "class TaskStatus"
import re
t = open(r"D:\111-1\AI_Scientist_v2\backend\app\database\models.py", encoding="utf-8").read()
print("=== 磁盘上 'class TaskStatus' 出现次数:", t.count("class TaskStatus"))

# 关键：模拟 _v2_pdf.py 的 import 顺序，看枚举会不会变
print("\n=== 模拟 _v2_pdf.py 的 import 顺序 ===")
import importlib

# 先像 _v2_pdf 那样：from app.api.v1.export import auto_export_pdf
from app.api.v1.export import auto_export_pdf
from app.database.models import AgentTask

col = AgentTask.__table__.c.status
print("  方式A (from export import fn):", [e.value for e in col.type.enum_class])

# 再 reload 看变化
importlib.reload(M)
print("  reload 后 AgentTask.status 枚举:", [e.value for e in AgentTask.__table__.c.status.type.enum_class])
