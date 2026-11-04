# Order pipeline (анти-потеря заявок)

Полный план и ТЗ лежат вне репозитория (`/workspace/altcam/order-pipeline/plan.md`, `codex-tz.md`); здесь — то, что нужно
для эксплуатации.

## Каналы, которые попадают в CRM (`inquiries`)

| Канал | Как | Источник (`source`) |
|---|---|---|
| Личный Telegram владельца @OficeITHelp (кнопки «Telegram» на сайте ведут сюда) | бот подключён через **Telegram Business** | `telegram_business` |
| Бот @AltCamSecurityUaBot (подписанные ссылки после формы/заказа `?start=o<id>_<sig>`, навигация канала) | личные сообщения боту | `bot` |
| Форма заявки `/site-lead` | сайт | `site_lead` |
| Кошик `/api/orders` | сайт | `site_order` |

## Что делает

* **Личный чат (Telegram Business):** клиент пишет человеку. Бот фиксирует запрос, один раз (если
  `BUSINESS_AUTOREPLY_ENABLED=true` и есть право «отвечать») отправляет от имени владельца подтверждение
  «Отримав, відповім протягом 5–10 хвилин.» (вне рабочих часов — «…завтра після 09:00»; текст — `BUSINESS_AUTOREPLY_TEXT`),
  присылает владельцу карточку и запускает напоминания. Когда владелец сам отвечает в этом чате — запрос помечается
  «Взята в работу», напоминания останавливаются. Других автоматических сообщений в личный чат бот не шлёт
  (follow-up и «посылка прибыла» приходят владельцу как подсказка). Шаблоны и ТТН из карточки уходят в личный чат
  только по нажатию владельца, простым текстом.
* **Бот:** автоответ с номером запроса, сроком ответа и кнопками FAQ (оплата / доставка / гарантия / позвать менеджера).
  Бот не выдаёт себя за человека. Капча и оферта не блокируют продажный диалог (`PIPELINE_CAPTURE_BEFORE_TERMS=true`).
* **Карточка владельцу:** взять в работу, ответить, шаблоны, наличие у поставщика, статус, оплата
  (предоплата / наложенный платёж), ТТН. Reply на карточку или копию сообщения — уходит клиенту.
* **Эскалация** без ответа (`REMINDER_MINUTES=5,15,60`, только в рабочие часы `WORK_HOURS`/`WORK_DAYS`/`BUSINESS_TIMEZONE`):
  1 — владелец, 2 — + второй контакт, 3 — + `SITE_LEAD_GROUP_ID`.
* **Follow-up** через `FOLLOWUP_HOURS` молчания после предложения (в боте — клиенту с кнопками; в личном чате — владельцу).
* **ТТН Новой почты:** номер уходит клиенту. Трекинг (`TrackingDocument.getStatusDocuments`) включается только при
  `NOVA_POSHTA_API_KEY`; без ключа задача не планируется (в логе: `Nova Poshta tracking disabled`), всё остальное работает.
* **Наличие:** Viatec — публичные XML-фиды (`<stock>` yes/few/no, кэш 30 мин), Yugtorg — API (`YUGTORG_API_KEY`).
  Закупочные цены не показываются.
* `/sla`, `/inq <id>` в боте и `GET /api/admin/inquiries` — открытые запросы и сколько ждут.

## Владелец и второй контакт без числовых ID

Если `ADMIN_CHAT_ID`/`ADMIN_IDS` и `SECOND_CONTACT_CHAT_ID` не заданы, роли назначаются автоматически:
пользователь с username из `OWNER_USERNAMES` (по умолчанию `OficeITHelp`) или `SECOND_CONTACT_USERNAMES`
(по умолчанию `uniwar`) нажимает **/start** в @AltCamSecurityUaBot → его chat_id сохраняется в `pipeline_contacts`,
бот отвечает «Вас зареєстровано як…» и показывает chat_id. Переменные окружения, если заданы, имеют приоритет.
Первая регистрация закрепляет роль; сменить — задать ID в env или удалить строку из `pipeline_contacts`.
Зарегистрированные контакты получают права менеджера в боте (кнопки карточек, `/sla`).

> Бот не может написать тому, кто ни разу не нажимал /start, — обоим нужно один раз открыть бота.

## Одноразовая настройка Telegram Business

1. **BotFather:** `/mybots` → @AltCamSecurityUaBot → *Bot Settings* → *Business Mode* → **Turn on**.
2. **Аккаунт @OficeITHelp** (телефон): *Настройки → Telegram для бизнеса (Telegram Business) → Чат-боты (Chatbots)* →
   ввести `@AltCamSecurityUaBot` → выбрать доступ к чатам (рекомендуется «Все личные чаты, кроме…» и исключить
   семью/друзей, либо «Не контакты» + «Новые чаты») → включить право **отвечать на сообщения** (нужно для
   подтверждения клиенту; без него бот только считает SLA).
3. Бот пришлёт в свой чат «✅ Бот підключено до вашого акаунта». Подключения других аккаунтов игнорируются
   (принимаются только владелец по `OWNER_USERNAMES`/`ADMIN_*`).
4. Исключить отдельные чаты из CRM можно и на стороне бота: `BUSINESS_IGNORE_CHAT_IDS=123,456`.

**allowed_updates:** polling запускается с `dp.resolve_used_update_types()`, поэтому Telegram присылает
`message`, `callback_query`, `business_connection`, `business_message` (используемые роутерами). Если когда-нибудь
перейти на webhook — передать тот же список в `setWebhook(allowed_updates=…)`. Требуется aiogram ≥ 3.20
(Bot API 9.0: `BusinessConnection.rights`), в `bot/requirements.txt` закреплён `aiogram==3.22.0`.

Проверено по core.telegram.org: подключать бизнес-бота может любой аккаунт (Premium не требуется); один бот на аккаунт;
ответ возможен в чатах, где клиент писал в последние 24 часа.

## Бесплатный keep-alive для Render Free

Render Free усыпляет веб-сервис через 15 минут без входящих HTTP-запросов (polling Telegram не считается) —
во сне бот не принимает сообщения и не шлёт напоминания. Без платного плана:

1. **UptimeRobot** (uptimerobot.com, бесплатно): *Add New Monitor* → тип **HTTP(s)** → URL
   `https://alt-cam-crm-api.onrender.com/health` → интервал **5 минут** → Create. Бонус — уведомление на email, если сервис упал.
2. Альтернатива — **cron-job.org** (бесплатно): *Create cronjob* → URL тот же → *Every 5 minutes* → Save.

Пинговать только `alt-cam-crm-api` (именно он делает polling и напоминания). Лимит Free — 750 инстанс-часов в месяц на
workspace: один постоянно бодрствующий сервис расходует ~720–744 ч, поэтому второй сервис (`alt-cam-manager-bot`)
не будить; если лимит исчерпан, Render останавливает Free-сервисы до конца месяца. Холодный старт после сна — ~1 мин.

## Статусы

`new → taken → stock_checked → offer_sent → confirmed → paid → supplier_ordered → supplier_paid → shipped → closed`,
`rejected` — из любого открытого. Вперёд с пропусками, назад на один шаг, `closed` только после оплаты.
Синхронизация в `web_orders` (`ordered_from_supplier`, `waiting_tracking`, `shipped`, `completed`, `canceled`).

## Деплой

1. Миграция `alembic/versions/20261104_0006_inquiries.py` (таблицы `inquiries`, `inquiry_events`, `pipeline_contacts`,
   `business_connections`) или `AUTO_CREATE_DB=true`.
2. Переменные: блок «Order pipeline» в `bot/.env.example` и `render.yaml`.
3. Напоминания — только на сервисе с polling (`ENABLE_BOT_POLLING=true`) или при `PIPELINE_SCHEDULER_ENABLED=true`.
4. Владелец и партнёр жмут /start в боте; настроить Telegram Business (выше) и keep-alive.

## Тесты

`python -m pytest tests/backend -q`; сквозные сценарии с реальной БД (в т.ч. Telegram Business и авторегистрация):
`TEST_PIPELINE_POSTGRES_URL=postgresql://postgres@localhost/postgres python -m pytest tests/backend/test_pipeline_db.py`.
