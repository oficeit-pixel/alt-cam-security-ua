# ALT-CAM cloud publisher

GitHub Actions runs the publisher every 30 minutes and publishes posts whose `scheduled_at` time has passed.

## Required GitHub Secrets

- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`
- `INSTAGRAM_USER_ID`
- `INSTAGRAM_ACCESS_TOKEN`
- `THREADS_USER_ID`
- `THREADS_ACCESS_TOKEN`

The workflow stores publication results in `social-posts/meta-automation/state.json` and commits that file back to the repository so posts are not duplicated.

Calendar page:

`https://oficeit-pixel.github.io/alt-cam-security-ua/social-posts/calendar/`
