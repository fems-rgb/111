"""widen agent_tasks.status to String(32) NOT NULL

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26

原因：模型定义 String(32), nullable=False，但旧库实际是 VARCHAR(14), nullable=True。
SQLite 用 ALTER ... 方式（batch op）修正。
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agent_tasks") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(14),
            type_=sa.String(32),
            existing_nullable=True,
            nullable=False,
            server_default="pending",
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_tasks") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(32),
            type_=sa.String(14),
            existing_nullable=False,
            nullable=True,
            server_default=None,
        )
