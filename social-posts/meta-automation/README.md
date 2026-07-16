# ALT-CAM social automation

Эта папка нужна для постоянной публикации постов ALT-CAM в Facebook, Instagram, Threads, Telegram и TikTok через официальные API.

## Что уже готово

- `posts.json` — календарь готовых публикаций.
- `publish_due.py` — скрипт, который публикует посты, время которых уже наступило.
- `.env.example` — шаблон настроек и токенов.
- `state.json` создаётся автоматически и хранит, что уже опубликовано.

## Почему нужен публичный URL картинки

Instagram, Threads и TikTok API принимают изображения через публичный `https://` URL. Поэтому картинки из `social-posts/images` должны быть доступны на сайте, например:

`https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/images/01-cameras-before-theft.png`

## Настройка

1. Скопировать `.env.example` в `.env`.
2. Заполнить:
   - `FACEBOOK_PAGE_ID`
   - `FACEBOOK_PAGE_ACCESS_TOKEN`
   - `INSTAGRAM_USER_ID`
   - `INSTAGRAM_ACCESS_TOKEN`
   - при необходимости `THREADS_USER_ID`
   - при необходимости `THREADS_ACCESS_TOKEN`
   - при необходимости `TELEGRAM_BOT_TOKEN`
   - при необходимости `TELEGRAM_CHAT_ID`
   - при необходимости `TIKTOK_ACCESS_TOKEN`
3. Установить зависимости:

```powershell
python -m pip install -r social-posts/meta-automation/requirements.txt
```

4. Проверить без публикации:

```powershell
python social-posts/meta-automation/publish_due.py --dry-run --force --post-id altcam-001-cameras-before-theft
```

5. Проверить токены и найти Instagram ID:

```powershell
python social-posts/meta-automation/check_setup.py
```

6. Когда токены проверены, в `.env` поставить:

```env
DRY_RUN=false
```

7. Опубликовать конкретный тестовый пост:

```powershell
python social-posts/meta-automation/publish_due.py --force --post-id altcam-001-cameras-before-theft
```

## Официальные документы Meta

- Instagram Content Publishing: https://developers.facebook.com/docs/instagram-platform/content-publishing/
- Facebook Pages API: https://developers.facebook.com/docs/pages-api/
- Threads Publishing API: https://developers.facebook.com/docs/threads/threads-api/publishing/
- Access Tokens: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/

## Telegram

1. Создать бота через `@BotFather`.
2. Добавить бота администратором в Telegram-канал или чат компании.
3. В `.env` или GitHub Secrets указать:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID` — например `@alt_cam_security_ua` или числовой chat id.
4. В нужных постах добавить платформу `"telegram"`.

Telegram публикует фото и подпись. Если подпись длиннее лимита Telegram для фото, скрипт отправит фото с короткой подписью и полный текст отдельным сообщением.

## TikTok

TikTok подключается через Content Posting API.

Нужно:

1. Аккаунт TikTok для ALT-CAM.
2. Приложение в TikTok for Developers.
3. Подключённый продукт Content Posting API.
4. OAuth-токен пользователя с `video.upload` для режима `MEDIA_UPLOAD` или `video.publish` для `DIRECT_POST`.
5. Подтверждённый домен/URL prefix для картинок, если TikTok забирает фото по ссылке.

Переменные:

- `TIKTOK_ACCESS_TOKEN`
- `TIKTOK_POST_MODE=MEDIA_UPLOAD` — безопасный стартовый режим: пост попадает в TikTok для финального подтверждения в приложении.
- `TIKTOK_POST_MODE=DIRECT_POST` — прямой постинг, только после одобрения Direct Post.
- `TIKTOK_PRIVACY_LEVEL=PUBLIC_TO_EVERYONE` — используется для Direct Post.

В нужных постах добавить платформу `"tiktok"`.

## Важное ограничение

Meta и TikTok не разрешают “тихо” создать токен без входа владельца аккаунта. Токен нужно получить через официальный кабинет разработчика / OAuth с нужными разрешениями. После этого публикация станет повторяемой и не будет зависеть от тяжёлых интерфейсов Meta Business Suite или TikTok.
