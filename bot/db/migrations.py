from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def migrate_web_orders(conn: AsyncConnection) -> None:
    statements = (
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(120)",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS tracking_provider VARCHAR(32)",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(64)",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS drive_folder_url VARCHAR(500)",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS supplier_order_number VARCHAR(120)",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS problem_note TEXT",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS assigned_admin_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL",
        "ALTER TABLE web_orders ADD COLUMN IF NOT EXISTS status_history JSONB NOT NULL DEFAULT '[]'::jsonb",
        "CREATE INDEX IF NOT EXISTS ix_web_orders_tracking_number ON web_orders (tracking_number)",
        "CREATE INDEX IF NOT EXISTS ix_web_orders_telegram_username ON web_orders (telegram_username)",
        "CREATE INDEX IF NOT EXISTS ix_web_orders_supplier_order_number ON web_orders (supplier_order_number)",
        "CREATE INDEX IF NOT EXISTS ix_web_orders_assigned_admin_id ON web_orders (assigned_admin_id)",
        "UPDATE web_orders SET status = 'clarification' WHERE status = 'confirmed'",
        "UPDATE web_orders SET status = 'ordered_from_supplier' WHERE status = 'awaiting_payment'",
        "UPDATE web_orders SET status = 'waiting_tracking' WHERE status = 'packing'",
    )
    for statement in statements:
        await conn.execute(text(statement))


async def migrate_admin_auth(conn: AsyncConnection) -> None:
    statements = (
        "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ",
        "ALTER TABLE admin_users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ",
        "UPDATE admin_users SET email_verified_at = COALESCE(email_verified_at, created_at, NOW()) WHERE active = TRUE",
    )
    for statement in statements:
        await conn.execute(text(statement))
