"""Bring legacy Alembic history up to the runtime schema.

Revision ID: 20260927_0004
Revises: 20260824_0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '20260927_0004'
down_revision = '20260824_0003'
branch_labels = depends_on = None


def upgrade():
    columns = [
        sa.Column('tracking_number', sa.String(120)),
        sa.Column('tracking_provider', sa.String(32)),
        sa.Column('telegram_username', sa.String(64)),
        sa.Column('drive_folder_url', sa.String(500)),
        sa.Column('supplier_order_number', sa.String(120)),
        sa.Column('problem_note', sa.Text()),
        sa.Column('assigned_admin_id', sa.Integer(), sa.ForeignKey('admin_users.id', ondelete='SET NULL')),
        sa.Column('status_history', JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    ]
    existing = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('web_orders')}
    for column in columns:
        if column.name not in existing: op.add_column('web_orders', column)
    for name in ('tracking_number', 'telegram_username', 'supplier_order_number', 'assigned_admin_id'):
        op.execute(sa.text(f'CREATE INDEX IF NOT EXISTS ix_web_orders_{name} ON web_orders ({name})'))
    op.execute('ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ')
    op.execute('ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ')
    op.execute('UPDATE admin_users SET email_verified_at = COALESCE(email_verified_at, created_at, NOW()) WHERE active = TRUE')
    for old,new in [('confirmed','clarification'),('awaiting_payment','ordered_from_supplier'),('packing','waiting_tracking')]:
        op.execute(sa.text('UPDATE web_orders SET status=:new WHERE status=:old').bindparams(new=new,old=old))
    # Explicit model creates the previously missing token table and its indexes.
    from bot.db.models import AdminAuthToken
    AdminAuthToken.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError('Destructive downgrade is not supported; restore a verified backup instead')
