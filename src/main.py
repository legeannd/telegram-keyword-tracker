"""Entry point for the Telegram Keyword Tracker."""

import asyncio
import logging
import os
import signal
import sys

from telethon import TelegramClient

from .config import load_config
from .database import Database
from .service import TrackerService
from .bot import setup_bot
from .listener import setup_listener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config()

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Initialize database
    db = Database("data/tracker.db")
    await db.initialize()

    # Create service
    service = TrackerService(db, config)

    # Create Telethon clients
    client = TelegramClient(config.session_path, config.api_id, config.api_hash)
    bot_client = TelegramClient("data/bot", config.api_id, config.api_hash)

    # Start listener: connect and check auth without triggering interactive prompt
    listener_configured = False
    await client.connect()
    if await client.is_user_authorized():
        listener_configured = True
        logger.info("Listener connected as user account.")
    else:
        await client.disconnect()
        logger.info("Listener not configured — skipping. Run setup to authenticate.")

    # Register handlers (pass listener state as a closure)
    await setup_listener(client, bot_client, service, config)
    await setup_bot(bot_client, client, service, config, is_listener_configured=lambda: listener_configured)

    await bot_client.start(bot_token=config.bot_token)
    logger.info("Telegram Keyword Tracker started.")
    logger.info("Bot connected and accepting commands.")
    logger.info("Owner ID: %d", config.owner_id)

    # Graceful shutdown
    shutdown_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received.")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    # On Windows, handle KeyboardInterrupt via the gather cancellation
    async def _run_until_done() -> None:
        """Run active clients until shutdown or disconnection."""
        tasks = [bot_client.run_until_disconnected()]
        if listener_configured:
            tasks.append(client.run_until_disconnected())
        run_task = asyncio.ensure_future(asyncio.gather(*tasks))
        shutdown_task = asyncio.ensure_future(shutdown_event.wait())

        done, pending = await asyncio.wait(
            [run_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    try:
        await _run_until_done()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupted.")
    finally:
        logger.info("Shutting down...")
        try:
            await client.disconnect()
        except Exception:
            pass
        try:
            await bot_client.disconnect()
        except Exception:
            pass
        await db.close()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
