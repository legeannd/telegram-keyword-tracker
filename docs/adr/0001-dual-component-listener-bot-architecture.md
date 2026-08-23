# Dual-component architecture: Listener (MTProto) + Bot (Bot API)

The system runs two Telegram connections in a single process: a Listener authenticated as the user's personal account via MTProto (Telethon), and a Bot created via @BotFather for command handling and notifications.

We chose this over a pure Bot API approach because bots can only see messages in groups where they're explicitly added as members, and cannot read channel messages without admin rights. The Listener sees every message the user's account receives — groups, channels, private chats — without any per-chat setup. The Bot exists solely as the user-facing interface (commands + notifications) because sending notifications from the user's own account (Saved Messages) would mix tracker alerts with personal bookmarks.

The trade-off: MTProto userbots operate in a grey area of Telegram's ToS. Aggressive automation or spammy behavior can get accounts restricted. Our use is passive (read-only listening, no automated replies or actions), which is low-risk, but the user should be aware.

Rejected alternatives:
- **Pure Bot API**: Would require manually adding the bot to every group/channel and granting permissions. Cannot monitor channels at all without admin. Defeats the "zero-setup monitoring" goal.
- **Saved Messages for notifications**: Simpler (one connection), but clutters the user's personal bookmark space and makes it impossible to separate tracker activity from normal Telegram use.
