"""Order pipeline: inquiries (SLA/state machine), inquiry_events, pipeline_contacts, business_connections."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261104_0006"
down_revision = "20260929_0005"
branch_labels = depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("inquiries"):
        op.create_table(
            "inquiries",
            sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
            sa.Column("source", sa.String(24), nullable=False),
            sa.Column("status", sa.String(32), server_default="new", nullable=False),
            sa.Column("client_tg_id", sa.BigInteger()),
            sa.Column("client_chat_id", sa.BigInteger()),
            sa.Column("client_username", sa.String(64)),
            sa.Column("client_name", sa.String(255)),
            sa.Column("business_connection_id", sa.String(64)),
            sa.Column("phone", sa.String(32)),
            sa.Column("summary", sa.Text(), server_default="", nullable=False),
            sa.Column("site_lead_id", sa.BigInteger(), sa.ForeignKey("site_leads.id", ondelete="SET NULL")),
            sa.Column("web_order_id", sa.Integer(), sa.ForeignKey("web_orders.id", ondelete="SET NULL")),
            sa.Column("payment_method", sa.String(16)),
            sa.Column("ttn", sa.String(32)),
            sa.Column("np_status_code", sa.String(8)),
            sa.Column("supplier_order_number", sa.String(120)),
            sa.Column("closed_reason", sa.Text()),
            sa.Column("awaiting_since", sa.DateTime(timezone=True)),
            sa.Column("reminder_level", sa.Integer(), server_default="0", nullable=False),
            sa.Column("first_response_at", sa.DateTime(timezone=True)),
            sa.Column("taken_at", sa.DateTime(timezone=True)),
            sa.Column("taken_by", sa.BigInteger()),
            sa.Column("last_client_msg_at", sa.DateTime(timezone=True)),
            sa.Column("last_owner_msg_at", sa.DateTime(timezone=True)),
            sa.Column("auto_reply_at", sa.DateTime(timezone=True)),
            sa.Column("followup_sent_at", sa.DateTime(timezone=True)),
            sa.Column("status_history", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        for name in ("source", "status", "client_tg_id", "phone", "site_lead_id", "web_order_id", "ttn", "awaiting_since", "created_at", "business_connection_id"):
            op.create_index(f"ix_inquiries_{name}", "inquiries", [name])
    if not inspector.has_table("inquiry_events"):
        op.create_table(
            "inquiry_events",
            sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
            sa.Column("inquiry_id", sa.BigInteger(), sa.ForeignKey("inquiries.id", ondelete="CASCADE"), nullable=False),
            sa.Column("kind", sa.String(32), nullable=False),
            sa.Column("actor", sa.String(16), nullable=False),
            sa.Column("text", sa.Text()),
            sa.Column("owner_chat_id", sa.BigInteger()),
            sa.Column("owner_message_id", sa.BigInteger()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        for name in ("inquiry_id", "kind", "owner_message_id", "created_at"):
            op.create_index(f"ix_inquiry_events_{name}", "inquiry_events", [name])
    if not inspector.has_table("pipeline_contacts"):
        op.create_table(
            "pipeline_contacts",
            sa.Column("role", sa.String(16), primary_key=True),
            sa.Column("chat_id", sa.BigInteger(), nullable=False),
            sa.Column("username", sa.String(64)),
            sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    if not inspector.has_table("business_connections"):
        op.create_table(
            "business_connections",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("user_chat_id", sa.BigInteger(), nullable=False),
            sa.Column("username", sa.String(64)),
            sa.Column("can_reply", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("allowed", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_business_connections_user_id", "business_connections", ["user_id"])


def downgrade():
    raise RuntimeError("Preserve CRM history: destructive downgrade requires a backup plan")
