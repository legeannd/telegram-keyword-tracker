# Telegram Keyword Tracker

A personal Telegram monitoring tool that scans all incoming messages for configured keywords and sends real-time alerts with links to the original messages.

## Language

**Listener**:
The MTProto client authenticated with the user's personal Telegram account, silently reading all incoming messages across groups, channels, and private chats.
_Avoid_: Userbot, client, monitor

**Bot**:
The @BotFather-created bot used for keyword management (commands) and delivering notifications to the user.
_Avoid_: Notification bot, management bot, assistant

**Keyword**:
A word or exact phrase the user wants to track. Matched case-insensitively as a whole unit using word boundaries.
_Avoid_: Filter, trigger, search term

**Match**:
A detected occurrence of a keyword in a message. Produces a notification to the user.
_Avoid_: Hit, alert, detection

**Notification**:
The Telegram message sent by the Bot to the user when a match occurs. Contains keyword, chat name, sender, snippet, and a link to the original message.
_Avoid_: Alert message, ping
