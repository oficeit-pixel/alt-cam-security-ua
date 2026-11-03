# AI-консультант «помічник ALT-CAM»

Ветка `feature/ai-consultant` (на основе `feature/order-pipeline`). Работает в чате бота и в личных чатах @OficeITHelp
(Telegram Business). Без `LLM_API_KEY` полностью выключен — конвейер работает как раньше.

## Что умеет
* Представляется «помічник ALT-CAM 🤖 — автоматичний консультант», никогда не выдаёт себя за человека
  (в личном чате каждое сообщение начинается с «🤖 Помічник ALT-CAM:»).
* Инструменты (function calling) только по реальным данным:
  `search_products` (catalog-data.js + цены `feeds/meta-catalog.csv` + ручные `price_overrides`),
  `check_stock` (фиды Viatec / API Yugtorg), `build_kit` (IP-камеры + NVR + HDD + PoE-комутатор + кабель),
  `create_cart_link` (`https://alt-cam.net.ua/catalog.html?cart=id:qty,...`), `get_policy` (тексты FAQ и
  `delivery-and-returns.html`), `handoff_to_manager`.
* Защита от выдумок: любая сумма «… грн» в ответе должна совпасть с ценой/итогом из инструментов (иначе ответ не
  отправляется → передача менеджеру); фразы со сроками («1–2 дні»), которых нет в опубликованных правилах, удаляются.
* Передача владельцу (без вызова LLM): оплата/реквизиты/счёт, злость/жалоба, просьба позвать человека/перезвонить;
  модель сама передаёт сложные задачи (монтаж, >16 камер, опт, гарантийные случаи). При передаче: клиенту
  «Передаю ваше питання менеджеру…», владельцу (и партнёру для оплаты/жалоб/просьб) — карточка «🤖➡️👤 AI передає
  розмову», AI в этом чате ставится на паузу, таймер напоминаний 5/15/60 запускается заново.
* Ответ AI считается ответом (`AI_COUNTS_AS_RESPONSE=true`): напоминания не дёргают владельца, пока AI справляется.
* Владелец ответил сам в личном чате → AI в этом чате на паузе (`AI_PAUSE_ON_OWNER_REPLY`).
* `/ai_off 123`, `/ai_on 123` (или ответом на карточку) и кнопка «🤖 AI вимк/увімк» в карточке.
* Free tier: интервал между запросами `AI_MIN_INTERVAL_SECONDS`, суточный лимит `AI_DAILY_REQUEST_LIMIT`,
  повтор при 429/5xx с учётом `Retry-After` (не дольше 12 с). Недоступен → клиенту стандартный автоответ /
  «передаю менеджеру», владельцу «⚠️ AI недоступний» (не чаще раза в 10 мин), паузы нет.

## Переменные
| Переменная | По умолчанию |
|---|---|
| `LLM_API_KEY` | — (обязателен; ключ Gemini из Google AI Studio) |
| `LLM_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai/` (любой OpenAI-совместимый) |
| `LLM_MODEL` | `gemini-3.5-flash-lite` (проверено 04.11.2026: ~1 с; `gemini-flash-latest` у этого ключа зависал >90 с) |
| `AI_ENABLED` / `AI_BUSINESS_ENABLED` | `true` / `true` |
| `AI_COUNTS_AS_RESPONSE` / `AI_PAUSE_ON_OWNER_REPLY` | `true` / `true` |
| `AI_MIN_INTERVAL_SECONDS` / `AI_DAILY_REQUEST_LIMIT` | `4` / `200` |
| `AI_TIMEOUT_SECONDS` / `AI_MAX_TOOL_ROUNDS` | `30` / `4` |

Миграция: `alembic/versions/20261104_0007_ai_chat_prefs.py` (таблица `ai_chat_prefs`).
Сайт: `cart-link.js` + обработка `?cart=` в `catalog.js` (товары добавляются в кошик, цены — из каталога и
повторно проверяются `/api/orders`).

## Проверка
* `python -m pytest tests/backend -q` (LLM замокан; ключи из окружения тестами игнорируются).
* Живой smoke: `LLM_API_KEY=… python scripts/ai_smoke.py "Потрібно 4 камери на будинок"`.
