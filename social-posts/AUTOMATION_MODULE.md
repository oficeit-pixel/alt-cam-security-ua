# Social automation module

This is the reusable publishing module created from the ALT-CAM automation work.

Use it when you need a second business direction, brand, niche, or client project with the same pipeline:

- content calendar in JSON;
- scheduled GitHub Actions publishing;
- Facebook Page;
- Instagram;
- Threads;
- Telegram;
- TikTok when approved;
- publication state tracking to avoid duplicates;
- setup checks and warnings.

## Create a new direction

Run from the repository root:

```powershell
python scripts/create_social_automation.py `
  --slug new-direction `
  --brand-name "New Direction Brand" `
  --facebook-page-id "1234567890" `
  --image-base-url "https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/new-direction-images" `
  --platforms facebook instagram threads telegram
```

The generator creates:

- `social-posts/new-direction-automation/`
- `social-posts/new-direction-images/`
- `.github/workflows/new-direction-publisher.yml`

## What changes for each new direction

Only these items should be different:

1. `posts.json` — dates, captions, platforms, media URLs.
2. Images folder — live media for that direction.
3. GitHub Secrets — tokens and chat IDs for that direction.
4. Optional workflow schedule.

Everything else is reusable.

## Secret naming

The generator uses a prefix based on the slug. For `new-direction`, the prefix is:

`NEW_DIRECTION_`

Example secrets:

- `NEW_DIRECTION_FACEBOOK_PAGE_ACCESS_TOKEN`
- `NEW_DIRECTION_INSTAGRAM_USER_ID`
- `NEW_DIRECTION_INSTAGRAM_ACCESS_TOKEN`
- `NEW_DIRECTION_THREADS_USER_ID`
- `NEW_DIRECTION_THREADS_ACCESS_TOKEN`
- `NEW_DIRECTION_TELEGRAM_BOT_TOKEN`
- `NEW_DIRECTION_TELEGRAM_CHAT_ID`
- `NEW_DIRECTION_TIKTOK_ACCESS_TOKEN`

This prevents one direction from accidentally using another direction's tokens.

## Meta/Facebook rule

Do not use a temporary Graph API Explorer token for production.

For every direction, create a Meta Business system user token and assign the correct Facebook Page to it. The generated folder includes `META_STABLE_TOKEN.md` with the full checklist.

## Testing

Local safe test:

```powershell
python social-posts/new-direction-automation/publish_due.py --dry-run
```

Cloud test:

1. Open GitHub Actions.
2. Select `New Direction Brand Social Publisher`.
3. Click `Run workflow`.
4. Check warnings and publication state.

## Current proven behavior

From the ALT-CAM implementation:

- Telegram works independently from Meta.
- Instagram / Threads can continue even if Facebook token expires.
- Facebook token issues are warnings when `FAIL_ON_PUBLISH_ERROR=false`.
- `state.json` prevents duplicated posts.
- GitHub Actions commits `state.json` back to the repository.
