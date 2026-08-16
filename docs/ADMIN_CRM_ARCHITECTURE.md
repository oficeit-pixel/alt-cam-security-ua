# ALT-CAM Admin / CRM architecture

## Recommended topology

- `/admin`: Next.js responsive application, deployed separately from the public static site.
- Existing Python service on Render: authenticated REST API, Telegram notifications and background jobs.
- PostgreSQL: products, price overrides, clients, orders, order items, notes, status history and audit events.
- Google Drive: binary documents only. PostgreSQL stores file IDs, ownership, type and retention date.
- Supplier synchronization: scheduled server job writes normalized products, then atomically publishes the site and Meta feeds from one dataset.

## Roles and access

- `Admin`: users, prices, imports, exports, deletion and configuration.
- `Manager`: clients, orders, notes, documents and status changes; no secrets or purchase-price export.
- Sign-in: Google OAuth restricted to an explicit email allowlist, mandatory Google 2FA, short server sessions in secure `HttpOnly` cookies.
- Every mutation writes an immutable audit event with actor, timestamp, entity, action and changed fields.

## Core entities

- `products`: supplier ID, SKU, title, real brand, category, specifications, retail and purchase prices, availability, image source, sync timestamp.
- `kits` and `kit_items`: ready solutions with quantities, installation items and public `price_from`.
- `clients`: name, normalized phone, city, Telegram ID and tags. Do not store unrelated personal data.
- `orders` and `order_items`: channel, status, manager, totals and timestamps.
- `order_notes`, `order_status_history`, `files`, `analytics_events`, `audit_log`.

## Order flow

`Нова → В роботі → Уточнення → Підтверджено → Виконано` or `Відмова`.

Orders from the catalog and Telegram enter the same table and receive an immutable public order number. Duplicate submissions are prevented with an idempotency key.

## Google Drive

Server-side Service Account with access only to the dedicated ALT-CAM root folder. No Drive credentials in browser JavaScript.

Folder layout:

`ALT-CAM Clients / YYYY / MM / Client-{client_id} / Order-{order_number}`

Names and phone numbers remain in PostgreSQL; Drive folder names use internal IDs. Subfolders: `01 Фото`, `02 Схеми`, `03 Кошториси`, `04 Договори та акти`.

## Security baseline

- HTTPS, strict CORS allowlist, CSRF protection, rate limits and request-size limits.
- Encrypt secrets in Render environment variables; rotate supplier, Google and Telegram credentials.
- Validate MIME type and scan uploads; prohibit executable files and public Drive sharing.
- Analytics uses random session IDs only; never send name, phone or message text.
- Data export/deletion workflow and configurable retention periods for client media.
- Nightly encrypted database backup and quarterly restore test.

## Delivery stages

1. Add migrations for web orders, order items, analytics, price overrides and audit log.
2. Protect existing catalog endpoints; add idempotency and database persistence.
3. Build admin authentication, orders and product management.
4. Add Drive document workflow and retention jobs.
5. Add dashboards, CSV/XLSX import/export and kit management.
