"""Durable site lead inbox."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260929_0005"
down_revision = "20260927_0004"
branch_labels = depends_on = None


def upgrade():
    if sa.inspect(op.get_bind()).has_table("site_leads"):
        return
    op.create_table("site_leads",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        *[sa.Column(name, sa.String(length), nullable=False) for name, length in (("type",100),("name",255),("phone",32),("email",255),("page",1000))],
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("ip_hash", sa.String(64)),
        sa.Column("telegram_sent", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("telegram_error", sa.Text()),
        sa.Column("telegram_delivered", JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False))
    for name in ("created_at", "telegram_sent"):
        op.create_index("ix_site_leads_" + name, "site_leads", [name])


def downgrade():
    raise RuntimeError("Preserve leads: destructive downgrade requires a backup plan")
