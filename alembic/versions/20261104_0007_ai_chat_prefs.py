"""AI consultant: per-client pause switch."""
from alembic import op
import sqlalchemy as sa

revision = "20261104_0007"
down_revision = "20261104_0006"
branch_labels = depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("ai_chat_prefs"):
        op.create_table(
            "ai_chat_prefs",
            sa.Column("client_tg_id", sa.BigInteger(), primary_key=True),
            sa.Column("paused", sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column("reason", sa.String(64)),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    op.drop_table("ai_chat_prefs")
