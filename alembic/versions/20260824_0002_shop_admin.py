"""web shop, analytics and price overrides

Revision ID: 20260824_0002
Revises: 20260726_0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_0002"
down_revision = "20260726_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_number", sa.String(32), nullable=False),
        sa.Column("customer", postgresql.JSONB(), nullable=False),
        sa.Column("delivery", postgresql.JSONB(), nullable=False),
        sa.Column("items", postgresql.JSONB(), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("manager_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_web_orders_order_number", "web_orders", ["order_number"], unique=True)
    op.create_index("ix_web_orders_status", "web_orders", ["status"])
    op.create_index("ix_web_orders_created_at", "web_orders", ["created_at"])
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("session_id", sa.String(128)),
        sa.Column("page", sa.String(255)),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_analytics_events_event", "analytics_events", ["event"])
    op.create_index("ix_analytics_events_session_id", "analytics_events", ["session_id"])
    op.create_index("ix_analytics_events_created_at", "analytics_events", ["created_at"])
    op.create_table(
        "price_overrides",
        sa.Column("product_id", sa.String(96), primary_key=True),
        sa.Column("price_uah", sa.Numeric(12, 2), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("price_overrides")
    op.drop_table("analytics_events")
    op.drop_table("web_orders")
