from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_id: int
    api_hash: str
    bot_token: str
    owner_id: int
    session_path: str
    disconnect_timeout: int
    snippet_length: int


def load_config() -> Config:
    """Load from env vars. Raises ValueError on missing required vars."""
    missing: list[str] = []

    api_id_raw = os.environ.get("TELEGRAM_API_ID")
    if not api_id_raw:
        missing.append("TELEGRAM_API_ID")

    api_hash = os.environ.get("TELEGRAM_API_HASH")
    if not api_hash:
        missing.append("TELEGRAM_API_HASH")

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")

    owner_id_raw = os.environ.get("TELEGRAM_OWNER_ID")
    if not owner_id_raw:
        missing.append("TELEGRAM_OWNER_ID")

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return Config(
        api_id=int(api_id_raw),  # type: ignore[arg-type]
        api_hash=api_hash,  # type: ignore[arg-type]
        bot_token=bot_token,  # type: ignore[arg-type]
        owner_id=int(owner_id_raw),  # type: ignore[arg-type]
        session_path=os.environ.get("SESSION_PATH", "data/listener"),
        disconnect_timeout=int(os.environ.get("DISCONNECT_TIMEOUT", "300")),
        snippet_length=int(os.environ.get("SNIPPET_LENGTH", "100")),
    )
