# Shared managers destination

Set `MANAGERS_CHAT_ID` on the backend to the numeric ID of the approved private
managers group (usually `-100...`). An invitation link is not a Bot API chat ID.
Obtain the ID with `/id@AltCamSecurityUaBot` in that group after deployment.
The bot must be a member with permission to send messages.

This destination receives initial inquiry cards, not just final SLA escalations.
Existing owner notifications remain enabled. Duplicate destinations are removed.
Only authorized numeric `ADMIN_IDS` can use management buttons; membership in
the group alone must never grant access to client replies or order changes.

Verification: create a clearly marked test inquiry in the bot and through the
site form; confirm each card reaches the approved group. Use Reply as an
authorized manager and verify client delivery. Do not send test supplier orders.

This is NOT an AI integration or an omnichannel inbox. Current automatic replies
are templates. Personal Telegram links, Instagram, WhatsApp and Viber require
separate inbound integrations. Do not claim these channels are connected, or
route visitors to an unverified bot destination. AI takeover/resume remains a
separate implementation requiring a configured provider and explicit conversation
ownership. Do not publish the private group invite as a client contact.
