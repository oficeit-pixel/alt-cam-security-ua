# Personal chat privacy

ALT-CAM serves clients through the website and the private bot chat. The managers
group mirrors client inquiries; it must not capture the owner's personal chats.

Keep `BUSINESS_ENABLED=false`, `BUSINESS_AUTOREPLY_ENABLED=false`, and
`AI_BUSINESS_ENABLED=false` in the deployment environment. Defaults and the Render
blueprint use these values. This does not disable the website AI, the private bot,
or manager handoff for those channels.

The master Business flag blocks incoming business messages and connection events,
AI responses, delivery for existing Business inquiries, and their background
reminders/follow-ups/tracking. Existing records are not deleted automatically.

For complete revocation, disconnect ALT-CAM under Telegram Settings > Telegram
Business > Chatbots on the owner's account. Server flags stop processing but do
not remove Telegram's connected-bot banner or revoke its permission.

Only isolated Business integration tests explicitly opt in. No real Telegram
messages or personal contacts are used by the regression tests.
