# Order pipeline (анти-потеря заявок)

Полный план и ТЗ: `/workspace/altcam/order-pipeline/plan.md`, `codex-tz.md` (вне репозитория).

## Что делает

* Любое личное сообщение клиента боту @AltCamSecurityUaBot, каждая заявка `/site-lead` и каждый заказ `/api/orders`
  создают запись `inquiries` (Neon) со статусом `new` и временем ожидания `awaiting_since`.
* Клиент сразу получает автоответ с номером запроса, ожидаемым временем ответа (рабочие часы `WORK_HOURS`, `WORK_DAYS`,
  `BUSINESS_TIMEZONE`) и кнопками FAQ: оплата / доставка / гарантия / позвать менеджера. Капча и оферта не блокируют
  продажный диалог (`PIPELINE_CAPTURE_BEFORE_TERMS=true`), уведомление о политике ПД — в автоответе.
* Владелец (`ADMIN_CHAT_ID`) получает карточку с кнопками: взять в работу, ответить, шаблоны ответов, наличие у поставщика,
  смена статуса, оплата (предоплата / наложенный платёж), ввод ТТН. Ответ свайпом (reply) на карточку или копию
  сообщения клиента пересылается клиенту.
* Эскалация без ответа (`REMINDER_MINUTES=5,15,60`, только в рабочие часы): 1 — владелец, 2 — + `SECOND_CONTACT_CHAT_ID`,
  3 — + `SITE_LEAD_GROUP_ID`. Защита от дублей — атомарный `UPDATE ... RETURNING`.
* Клиент молчит `FOLLOWUP_HOURS` после предложения — одно напоминание с кнопками «Підтверджую / Є питання / Неактуально».
* ТТН Новой почты: клиент получает номер, бот опрашивает `TrackingDocument.getStatusDocuments` (`NOVA_POSHTA_API_KEY`),
  сообщает клиенту о прибытии, закрывает запрос при получении, алертит владельца при отказе.
* `/sla` в боте и `GET /api/admin/inquiries` — список открытых запросов, кто сколько ждёт.
* Наличие: Viatec — публичные XML-фиды из `catalog-sync/config.json` (`<stock>` yes/few/no, кэш 30 мин);
  Yugtorg — `b2b.yugtorg.com/apiservices/export/product` (`YUGTORG_API_KEY`, поле `count`). Закупочные цены не показываются.

## Статусы

`new → taken → stock_checked → offer_sent → confirmed → paid → supplier_ordered → supplier_paid → shipped → closed`,
`rejected` — из любого открытого. Вперёд можно с пропусками, назад — на один шаг, `closed` только после оплаты.
Статусы синхронизируются в `web_orders` (`ordered_from_supplier`, `waiting_tracking`, `shipped`, `completed`, `canceled`).

## Деплой

1. Миграция `alembic/versions/20261104_0006_inquiries.py` (или `AUTO_CREATE_DB=true` — `create_all` создаст таблицы).
2. Переменные: см. `bot/.env.example` (блок «Order pipeline») и `render.yaml`.
3. Напоминания работают только там, где включён polling (`ENABLE_BOT_POLLING=true`) или `PIPELINE_SCHEDULER_ENABLED=true`.
   На Render Free сервис засыпает через 15 минут без HTTP-трафика — для надёжных напоминаний нужен платный инстанс.

## Тесты

`python -m pytest tests/backend -q`; сквозные сценарии с реальной БД:
`TEST_PIPELINE_POSTGRES_URL=postgresql://postgres@localhost/postgres python -m pytest tests/backend/test_pipeline_db.py`.
