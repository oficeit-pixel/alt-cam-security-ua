# ALT-CAM Meta automation

Эта папка нужна для постоянной публикации постов ALT-CAM в Facebook, Instagram и Threads через официальные API Meta.

## Что уже готово

- `posts.json` — календарь из 9 готовых публикаций.
- `publish_due.py` — скрипт, который публикует посты, время которых уже наступило.
- `.env.example` — шаблон настроек и токенов.
- `state.json` создаётся автоматически и хранит, что уже опубликовано.

## Почему нужен публичный URL картинки

Instagram и Threads API принимают изображения через публичный `https://` URL. Поэтому картинки из `social-posts/images` должны быть доступны на сайте, например:

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

## Важное ограничение

Meta не разрешает “тихо” создать токен без входа владельца аккаунта. Токен нужно получить через Meta Developer / Graph API Explorer / приложение Meta с нужными разрешениями. После этого публикация станет повторяемой и не будет зависеть от тяжёлого интерфейса Meta Business Suite.
