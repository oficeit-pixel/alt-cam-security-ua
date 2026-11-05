# AI-консультант «помічник ALT-CAM»

Один консультант (модуль `bot/ai/`, Gemini через OpenAI-совместимый endpoint) обслуживает три канала:

| Канал | Где подключено |
|---|---|
| Чат-виджет на сайте (`ai-chat.js` на `index.html`, `catalog.html`) | `POST /api/ai/chat`, `GET /api/ai/status` (`bot/web/ai_chat.py`) на `alt-cam-crm-api` |
| Чат бота @AltCamSecurityUaBot | `bot/handlers/pipeline_client.py` → `bot.ai.runtime.respond` |
| Личные чаты владельца (Telegram Business) | `bot/handlers/pipeline_business.py` → `bot.ai.runtime.respond(business=True)` |

Выключен, пока не заданы **оба** `AI_CONSULTANT_ENABLED=true` и `GEMINI_API_KEY`. Без них: виджет на сайте не
показывается (status → `enabled:false`), бот и Business работают как раньше (стандартный автоответ + карточка владельцу).

## Поведение
* Не выдаёт себя за человека, не придумывает имя, но и сам не сообщает, что он бот. Если клиент прямо спрашивает
  «ты бот?» — честно отвечает, что это автоматический помощник ALT-CAM и может подключиться менеджер.
  `AI_DISCLOSE_BOT=true` возвращает явное приветствие «🤖 автоматичний консультант» и префикс в Business-чатах.
* Язык ответа — язык клиента (украинский по умолчанию, русский если клиент пишет по-русски); приветствие и
  сообщение о передаче менеджеру тоже локализованы.
* Инструменты только по реальным данным: `search_products`, `check_stock`, `build_kit`, `create_cart_link`,
  `get_policy`, `handoff_to_manager`. Любая сумма «… грн» в ответе должна совпасть с данными инструментов.
* Комплект видеонаблюдения: `build_kit` выбирает в первую очередь регистратор с достаточным числом встроенных PoE-портов
  (`poe_ports`) и в этом случае **не** предлагает PoE-коммутатор (`poe_switch_needed=false`). Если коммутатор нужен,
  подбирается по числу камер, которые регистратор не запитывает. `create_cart_link` дополнительно убирает из корзины
  PoE-коммутатор, если регистратор в той же корзине сам питает все камеры.
* Передача менеджеру (оплата, злость, просьба позвать человека, сложные задачи): в Telegram — карточка владельцу и
  пауза AI в этом чате; на сайте — форма «телефон» → обычный `/site-lead` с перепиской (попадает в CRM/конвейер) и
  ссылка «продовжити в Telegram».
* Free tier: интервал `AI_MIN_INTERVAL_SECONDS`, суточный лимит `AI_DAILY_REQUEST_LIMIT`, ретраи 429/5xx; сайт
  дополнительно ограничен `AI_WEB_RATE_PER_MINUTE` запросами в минуту с одного IP. Gemini недоступен → клиенту
  стандартный ответ/«передаю менеджеру», сайт не ломается.

## Переменные окружения (Render → alt-cam-crm-api)
| Переменная | По умолчанию | |
|---|---|---|
| `AI_CONSULTANT_ENABLED` | `false` | **обязательно** `true` для включения (старое имя `AI_ENABLED` тоже принимается) |
| `GEMINI_API_KEY` | — | **обязательно**, ключ Google AI Studio (free tier); алиас `LLM_API_KEY` |
| `LLM_MODEL` | `gemini-3.5-flash-lite` | |
| `LLM_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai/` | |
| `AI_WEB_CHAT_ENABLED` | `true` | виджет на сайте |
| `AI_BUSINESS_ENABLED` | `true` | ответы в Telegram Business |
| `AI_DISCLOSE_BOT` | `false` | явно представляться ботом |
| `AI_WEB_RATE_PER_MINUTE` | `6` | |
| `AI_COUNTS_AS_RESPONSE` / `AI_PAUSE_ON_OWNER_REPLY` | `true` / `true` | |
| `AI_MIN_INTERVAL_SECONDS` / `AI_DAILY_REQUEST_LIMIT` | `4` / `200` | |
| `AI_TIMEOUT_SECONDS` / `AI_MAX_TOOL_ROUNDS` | `30` / `4` | |

Миграция: `alembic/versions/20261104_0007_ai_chat_prefs.py` (таблица `ai_chat_prefs`).
Сайт: `cart-link.js` + `?cart=` в `catalog.js`, `ai-chat.js` (виджет).

## Проверка
* `python -m pytest tests/backend -q` (LLM замокан; ключи из окружения тестами игнорируются).
* Живой smoke: `AI_CONSULTANT_ENABLED=true GEMINI_API_KEY=… python scripts/ai_smoke.py "Потрібно 4 камери на будинок"`.
