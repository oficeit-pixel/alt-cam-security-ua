"""initial schema

Revision ID: 20260726_0001
Revises:
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260726_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role = postgresql.ENUM("client", "installer", "admin", name="userrole", create_type=False)
order_status = postgresql.ENUM(
    "draft",
    "published",
    "in_progress",
    "completed",
    "canceled",
    name="orderstatus",
    create_type=False,
)
bid_status = postgresql.ENUM("pending", "accepted", "rejected", name="bidstatus", create_type=False)


def upgrade() -> None:
    user_role.create(op.get_bind(), checkfirst=True)
    order_status.create(op.get_bind(), checkfirst=True)
    bid_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("full_name", sa.String(length=255)),
        sa.Column("phone", sa.String(length=255)),
        sa.Column("accepted_terms", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "installer_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fop_code", sa.String(length=64)),
        sa.Column("test_score", sa.Integer()),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("portfolio_photos", postgresql.JSONB(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("object_type", sa.String(length=128), nullable=False),
        sa.Column("points_count", sa.String(length=64), nullable=False),
        sa.Column("require_ups", sa.Boolean(), nullable=False),
        sa.Column("photos", postgresql.JSONB(), nullable=False),
        sa.Column("estimated_price_min", sa.Integer()),
        sa.Column("estimated_price_max", sa.Integer()),
        sa.Column("status", order_status, nullable=False),
        sa.Column("selected_installer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "order_bids",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("installer_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_offer", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("status", bid_status, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("order_bids")
    op.drop_table("orders")
    op.drop_table("installer_profiles")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
    bid_status.drop(op.get_bind(), checkfirst=True)
    order_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
