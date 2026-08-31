# ALT-CAM CRM — серверні інтеграції

Секрети додаються тільки в Render → Environment. У репозиторій значення не записуються.

## Google Drive

1. Створити Service Account у Google Cloud і ввімкнути Google Drive API.
2. Надати email Service Account доступ редактора до кореневої папки `ALT-CAM Clients`.
3. Додати в Render:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` — повний JSON ключа;
   - `GOOGLE_DRIVE_FOLDER_ID` — ID папки `ALT-CAM Clients`.

Для нового замовлення автоматично створюється структура:

`ALT-CAM Clients / Рік / Місяць / Ім’я-Телефон / WEB-XXXXXXXX-XXXXXX`

## Укрпошта

Окремий ключ статус-трекінгу потрібно отримати в Укрпошти. Додати в Render:

- `UKRPOSHTA_TRACKING_TOKEN`;
- `UKRPOSHTA_API_URL=https://www.ukrposhta.ua/ecom/0.0.1` — змінювати лише за документацією Укрпошти.

У картці замовлення кнопка оновлення з’являється, коли вибрано «Укрпошта» і задано трек-номер.

## Пошта постачальників

Використовується IMAP тільки на сервері. Додати в Render:

- `IMAP_HOST=imap.gmail.com`;
- `IMAP_PORT=993`;
- `IMAP_USER`;
- `IMAP_PASSWORD` — пароль застосунку, не основний пароль пошти;
- `IMAP_FOLDER=INBOX`;
- `SUPPLIER_EMAIL_SENDERS` — дозволені адреси через кому.

Синхронізація читає до 50 нових листів, обробляє тільки дозволених відправників, витягує номер `WEB-...` і трек. Текст листа та вкладення в базі не зберігаються.
