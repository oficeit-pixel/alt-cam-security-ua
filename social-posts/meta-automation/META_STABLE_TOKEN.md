# Stable Meta token for ALT-CAM automation

The social publisher should not use a short-lived Facebook token copied from Graph API Explorer for production posting. Explorer tokens are useful for testing, but they expire and can lose Page access.

Use a Meta Business system user token for the Facebook Page instead.

## One-time setup

1. Open Meta Business Settings for the ALT-CAM business.
2. Go to **Users → System users**.
3. Create a system user named `ALT-CAM Social Publisher`.
4. Assign the Facebook Page `Alt-Cam Security UA` to this system user.
5. Give the system user Page permissions needed for publishing:
   - create and manage content;
   - read Page engagement;
   - view Page list / Page access.
6. Generate an access token for the app `ALT-CAM Social Publisher`.
7. Include these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
8. Store the generated token in GitHub Actions secret:
   - `FACEBOOK_PAGE_ACCESS_TOKEN`

## Validation

After updating the secret, run the GitHub Actions workflow:

`ALT-CAM Social Publisher → Run workflow`

The `Check publisher setup` step should show that the Facebook Page token can read Page `962902993572061`.

## Important notes

- Do not paste tokens into chat messages.
- If Meta asks which Page the app can access, choose the ALT-CAM Page.
- If `/me/accounts` returns an empty list, the current token does not have Page access and must not be used for automation.
- Keep `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Secrets; Telegram already works independently of Meta.
