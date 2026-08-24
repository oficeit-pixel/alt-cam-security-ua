"""admin users and audit log

Revision ID: 20260824_0003
Revises: 20260824_0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_0003"
down_revision = "20260824_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(180), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)
    op.create_index("ix_admin_users_active", "admin_users", ["active"])
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admin_users.id", ondelete="SET NULL")),
        sa.Column("admin_email", sa.String(180), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(64)),
        sa.Column("entity_id", sa.String(96)),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admin_audit_logs_admin_id", "admin_audit_logs", ["admin_id"])
    op.create_index("ix_admin_audit_logs_admin_email", "admin_audit_logs", ["admin_email"])
    op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"])
    op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("admin_audit_logs")
    op.drop_table("admin_users")
