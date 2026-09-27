# Отчёт: подготовка перехода ALT-CAM на Neon

Дата: 27.09.2026. Ветка: `fix/neon-db`, исходный main: `26e29e1`.
Ни push, ни деплой, ни изменение Render/Neon/секретов не выполнялись.

## По пунктам задания

1. `normalize_database_url` переводит postgres/postgresql в asyncpg, удаляет
   sslmode/channel_binding, сохраняет требуемый SSL. Pooler получает два отключённых
   statement cache и предупреждение без URL. Пул: pre_ping, recycle=300, 5+5.
2. Инициализация: пять попыток, паузы 2/4/8/16 секунд, предел 20 секунд на попытку.
   После неудачи web запускается. Backfill имеет отдельный перехват ошибок и
   timeout=10 секунд. Health выполняет SELECT 1 с timeout=5, всегда возвращает
   HTTP 200 с `ok:true` и фактическим `db`. Логи не выводят тексты ошибок соединения.
3. Основной путь схемы — существующий create_all + runtime migrations при
   AUTO_CREATE_DB=true. Исправлен явный импорт моделей. Alembic нормализует URL;
   добавлена ревизия 0004 для отсутствовавших полей CRM и admin_auth_tokens.
   Реальный прогон обоих путей на PostgreSQL 17 пока **не выполнен**: Docker на
   этом ПК отсутствует. Подготовлены изолированные тесты и CI с postgres:17.
4. Bash/PowerShell запускают общий Python-скрипт pg_dump/pg_restore. URL — только
   окружение, subprocess stderr не раскрывается. Восстановление транзакционное,
   требуется CONFIRM_NEON_RESTORE=YES, сравниваются все пользовательские таблицы,
   sequences выравниваются. Скрипт на реальных данных **не запускался**.
5. DATABASE_URL остаётся sync:false в обоих сервисах. Привязок fromDatabase и
   databases не было. Polling включён только у CRM, отключён у manager и в старом
   bot/render.yaml. Добавлены buildFilter.paths. Telegram updates не сбрасываются.
6. Три publisher workflow добавляют `[skip render]` к сообщению коммита.
7. `.env.example` содержит только пример Neon URL и флаг polling.

## Проверено

- `python -m pytest tests/backend -q`: **14 passed, 2 skipped**.
- Два skipped — PostgreSQL 17, а не успешно пройденная проверка БД.
- Реальный HTTP-сервер с недоступной БД localhost:1: HTTP 200, db:false.
- Тест main: после неудачной инициализации web остаётся запущенным, отключённый
  polling не вызывает Telegram delete_webhook.
- Нормализация, pooler, URL-encoded пароль, повторы, отсутствие секретов в логе,
  успешный mocked SELECT 1, защита скрипта переноса покрыты тестами.
- compileall и git diff --check пройдены.

Ограничения: нет доказательства миграции реальных данных, запуска на PostgreSQL 17
или соединения с пользовательским Neon. Перед слиянием обязателен полный прогон
интеграционных тестов. Единственное предупреждение pytest — существующее
DeprecationWarning об AiohttpSession из зависимости.

Формат Render DATABASE_URL, перенос и послепубликационный чеклист — раздел
«Перенос базы в Neon» в README.md. Старая Render-база приостановлена; без её
восстановления или бэкапа возможен только запуск с пустой базой, не перенос данных.
