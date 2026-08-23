"""MTProto listener for incoming messages across all chats."""

import hashlib
import logging
import time

from telethon import TelegramClient, events
from telethon.tl.types import User as TlUser, Channel, Chat

from .config import Config
from .service import TrackerService

logger = logging.getLogger(__name__)

# In-memory dedup: (chat_id, msg_id) -> (text_hash, timestamp)
# Prevents duplicate notifications when Telegram fires both
# NewMessage and MessageEdited for the same channel post.
_DEDUP_WINDOW = 60  # seconds
_recent_notifications: dict[tuple[int, int], tuple[str, float]] = {}


def _get_chat_title(chat) -> str | None:
    """Extract chat title from a chat entity."""
    if isinstance(chat, (Channel, Chat)):
        return chat.title
    if isinstance(chat, TlUser):
        parts = [chat.first_name or "", chat.last_name or ""]
        name = " ".join(p for p in parts if p)
        return name or None
    return None


def _get_chat_username(chat) -> str | None:
    """Extract username from a chat entity."""
    return getattr(chat, "username", None)


def _get_sender_name(sender) -> str | None:
    """Extract display name from a sender entity."""
    if sender is None:
        return None
    if isinstance(sender, TlUser):
        parts = [sender.first_name or "", sender.last_name or ""]
        name = " ".join(p for p in parts if p)
        return name or None
    if isinstance(sender, (Channel, Chat)):
        return sender.title
    return None


def _get_sender_username(sender) -> str | None:
    """Extract username from a sender entity."""
    if sender is None:
        return None
    return getattr(sender, "username", None)


async def setup_listener(
    client: TelegramClient,
    bot_client: TelegramClient,
    service: TrackerService,
    config: Config,
) -> None:
    """Register message handlers on the user's MTProto client."""

    # Extract bot's user ID from token (number before the colon)
    bot_id = int(config.bot_token.split(":")[0])

    async def _process_message(event, is_edit: bool) -> None:
        """Common processing for new messages and edits."""
        message = event.message

        # Skip service messages
        if message.action is not None:
            return

        # Skip own messages
        if message.out:
            return

        # Skip messages from our bot (prevents recursive scanning)
        if message.sender_id == bot_id:
            return

        # Get text (message text or caption)
        text = message.text or ""
        if not text:
            return

        # Dedup: skip if we already notified for this exact message text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        msg_key = (event.chat_id, message.id)
        now = time.monotonic()

        # Prune old entries
        stale = [k for k, (_, ts) in _recent_notifications.items() if now - ts > _DEDUP_WINDOW]
        for k in stale:
            del _recent_notifications[k]

        prev = _recent_notifications.get(msg_key)
        if prev is not None:
            prev_hash, _ = prev
            if prev_hash == text_hash:
                # Same message, same text — duplicate event, skip
                return
            # Different text — real edit, let it through
            is_edit = True

        _recent_notifications[msg_key] = (text_hash, now)

        # Get chat info
        chat = await event.get_chat()
        chat_title = _get_chat_title(chat)
        chat_username = _get_chat_username(chat)
        chat_id = event.chat_id

        # Skip blacklisted chats
        if await service.is_blacklisted(chat_title, chat_username):
            return

        # Get sender info
        sender = await event.get_sender()
        sender_name = _get_sender_name(sender)
        sender_username = _get_sender_username(sender)

        # Fetch current keywords and scan
        keywords = await service.list_keywords()
        notification = service.scan_message(
            text=text,
            chat_id=chat_id,
            chat_title=chat_title,
            message_id=message.id,
            sender_name=sender_name,
            sender_username=sender_username,
            is_edit=is_edit,
            chat_username=chat_username,
            keywords=keywords,
        )

        if notification:
            try:
                await bot_client.send_message(
                    config.owner_id, notification, link_preview=False
                )
            except Exception as e:
                logger.error("Failed to send notification: %s", e)

    @client.on(events.NewMessage())
    async def handle_new_message(event: events.NewMessage.Event) -> None:
        try:
            await _process_message(event, is_edit=False)
        except Exception as e:
            logger.error("Error processing new message: %s", e)

    @client.on(events.MessageEdited())
    async def handle_message_edited(event: events.MessageEdited.Event) -> None:
        try:
            await _process_message(event, is_edit=True)
        except Exception as e:
            logger.error("Error processing edited message: %s", e)

    # Disconnect monitoring background task
    async def _monitor_connection() -> None:
        """Monitor connection state and alert on prolonged disconnection."""
        last_connected_time = time.monotonic()
        warning_sent = False

        while True:
            await asyncio.sleep(30)  # Check every 30 seconds

            if client.is_connected():
                if warning_sent:
                    # Reconnected after a warning — notify
                    try:
                        await bot_client.send_message(
                            config.owner_id,
                            "✅ **Listener reconnected.** Monitoring resumed.",
                            link_preview=False,
                        )
                    except Exception as e:
                        logger.error("Failed to send reconnect notice: %s", e)
                    warning_sent = False
                last_connected_time = time.monotonic()
            else:
                elapsed = time.monotonic() - last_connected_time
                if elapsed > config.disconnect_timeout and not warning_sent:
                    try:
                        minutes = int(elapsed // 60)
                        await bot_client.send_message(
                            config.owner_id,
                            f"⚠️ **Listener disconnected** for {minutes}+ minutes. "
                            "Keyword monitoring is paused until reconnection.",
                            link_preview=False,
                        )
                        warning_sent = True
                    except Exception as e:
                        logger.error("Failed to send disconnect warning: %s", e)

    # Start the monitoring task — it will run in the background
    asyncio.ensure_future(_monitor_connection())
