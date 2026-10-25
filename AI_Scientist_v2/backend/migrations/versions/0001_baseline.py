"""baseline: full schema from Base.metadata

Revision ID: 0001
Revises:
Create Date: 2026-10-26

策略：
- 直接以 Base.metadata.create_all 建立全量初始 schema（幂等，已存在的表会跳过）
- 对已有 zhixing.db：请 `alembic stamp head` 把当前 DB 标记为已应用 0001，
  之后新增 revision 走标准 autogenerate
- 对空 DB：`alembic upgrade head` 一步建全
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# ── 引入项目元数据 ──
from app.database.session import Base
from app.database import models  # noqa: F401  确保所有类注册到 Base.metadata

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # 幂等：checkfirst=True 是 create_all 默认，跳过已存在表
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # 谨慎：baseline 反向操作会 drop 全库；仅开发环境使用
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
