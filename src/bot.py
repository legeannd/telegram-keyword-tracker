"""Bot command handlers for the Telegram Keyword Tracker."""


from telethon import TelegramClient, events

from .config import Config
from .service import TrackerService


async def setup_bot(
    bot_client: TelegramClient,
    listener_client: TelegramClient,
    service: TrackerService,
    config: Config,
    is_listener_configured: callable = None,
) -> None:
    """Register all command handlers on the bot client."""

    @bot_client.on(events.NewMessage(pattern=r"^/start$"))
    async def handle_start(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        await event.respond(
            "🔍 **Telegram Keyword Tracker**\n\n"
            "I'll notify you when your tracked keywords appear in any chat "
            "your user account is part of.\n\n"
            "**Commands:**\n"
            "/add <phrase> — Track a new keyword\n"
            "/remove <phrase> — Stop tracking a keyword\n"
            "/list — Show all tracked keywords\n"
            "/status — Check listener connection status\n"
            "/help — Command reference"
        )

    @bot_client.on(events.NewMessage(pattern=r"^/add(\s|$)"))
    async def handle_add(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        text = event.message.text or ""
        phrase = text[len("/add"):].strip()
        if not phrase:
            await event.respond("**Usage:** `/add <phrase>`\n\nExample: `/add bitcoin`")
            return
        try:
            keyword = await service.add_keyword(phrase)
            await event.respond(f"✅ Now tracking: **{keyword}**")
        except ValueError as e:
            await event.respond(f"⚠️ {e}")

    @bot_client.on(events.NewMessage(pattern=r"^/remove(\s|$)"))
    async def handle_remove(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        text = event.message.text or ""
        phrase = text[len("/remove"):].strip()
        if not phrase:
            await event.respond("**Usage:** `/remove <phrase>`\n\nExample: `/remove bitcoin`")
            return
        removed = await service.remove_keyword(phrase)
        if removed:
            await event.respond(f"✅ Removed: **{phrase}**")
        else:
            await event.respond(f"⚠️ Keyword not found: **{phrase}**")

    @bot_client.on(events.NewMessage(pattern=r"^/list$"))
    async def handle_list(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        keywords = await service.list_keywords()
        if not keywords:
            await event.respond("No keywords configured.\n\nUse `/add <phrase>` to start tracking.")
            return
        lines = ["**Tracked keywords:**\n"]
        for i, kw in enumerate(keywords, 1):
            lines.append(f"{i}. `{kw}`")
        await event.respond("\n".join(lines))

    @bot_client.on(events.NewMessage(pattern=r"^/status$"))
    async def handle_status(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return

        configured = is_listener_configured() if is_listener_configured else False

        if not configured:
            await event.respond(
                "⚙️ **Listener not configured.**\n\n"
                "You need to run the initial setup to connect your Telegram account.\n"
                "Run the application in a terminal to complete phone authentication."
            )
            return

        connected = listener_client.is_connected()
        keywords = await service.list_keywords()

        if connected:
            status = "✅ **Listener is connected** and monitoring messages."
        else:
            status = "❌ **Listener is disconnected.** Keyword monitoring is paused."

        status += f"\n\n📊 Tracking **{len(keywords)}** keyword(s)."
        await event.respond(status)


    @bot_client.on(events.NewMessage(pattern=r"^/blacklist(\s|$)"))
    async def handle_blacklist(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        text = event.message.text or ""
        name = text[len("/blacklist"):].strip()
        if not name:
            await event.respond(
                "**Usage:** `/blacklist <chat name or username>`\n\n"
                "Example: `/blacklist Gaming Deals` or `/blacklist dealbot`"
            )
            return
        try:
            added = await service.add_blacklist(name)
            await event.respond(f"✅ Blacklisted: **{added}**")
        except ValueError as e:
            await event.respond(f"⚠️ {e}")

    @bot_client.on(events.NewMessage(pattern=r"^/unblacklist(\s|$)"))
    async def handle_unblacklist(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        text = event.message.text or ""
        name = text[len("/unblacklist"):].strip()
        if not name:
            await event.respond("**Usage:** `/unblacklist <chat name or username>`")
            return
        removed = await service.remove_blacklist(name)
        if removed:
            await event.respond(f"✅ Removed from blacklist: **{name}**")
        else:
            await event.respond(f"⚠️ Not found in blacklist: **{name}**")

    @bot_client.on(events.NewMessage(pattern=r"^/blacklisted$"))
    async def handle_blacklisted(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        entries = await service.list_blacklist()
        if not entries:
            await event.respond("No chats blacklisted.")
            return
        lines = ["**Blacklisted chats:**\n"]
        for i, name in enumerate(entries, 1):
            lines.append(f"{i}. `{name}`")
        await event.respond("\n".join(lines))

    @bot_client.on(events.NewMessage(pattern=r"^/help$"))
    async def handle_help(event: events.NewMessage.Event) -> None:
        if event.sender_id != config.owner_id:
            return
        await event.respond(
            "**Command Reference:**\n\n"
            "`/add <phrase>` — Track a keyword or phrase.\n\n"
            "`/remove <phrase>` — Stop tracking a keyword.\n\n"
            "`/list` — List all tracked keywords.\n\n"
            "`/blacklist <name>` — Ignore a chat by title or username.\n\n"
            "`/unblacklist <name>` — Stop ignoring a chat.\n\n"
            "`/blacklisted` — Show all blacklisted chats.\n\n"
            "`/status` — Check if the listener is connected.\n\n"
            "`/help` — Show this message.\n\n"
            "**How it works:**\n"
            "Your user account listens to all chats it's in. "
            "When a message contains a tracked keyword, "
            "I'll send you a notification here."
        )
