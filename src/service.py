"""Keyword CRUD, message scanning, and notification formatting."""

from __future__ import annotations

import re

from .config import Config
from .database import Database


class TrackerService:
    def __init__(self, db: Database, config: Config) -> None:
        self._db = db
        self.config = config

    async def add_keyword(self, phrase: str) -> str:
        normalized = phrase.strip()
        if not normalized:
            raise ValueError("Keyword cannot be empty")
        existing = await self._db.list_keywords()
        for kw in existing:
            if kw.lower() == normalized.lower():
                raise ValueError(f"Keyword '{normalized}' already exists")
        await self._db.add_keyword(normalized)
        return normalized

    async def remove_keyword(self, phrase: str) -> bool:
        return await self._db.remove_keyword(phrase.strip())

    async def list_keywords(self) -> list[str]:
        return await self._db.list_keywords()

    async def add_blacklist(self, name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Chat name cannot be empty")
        existing = await self._db.list_blacklist()
        for entry in existing:
            if entry.lower() == normalized.lower():
                raise ValueError(f"'{normalized}' is already blacklisted")
        await self._db.add_blacklist(normalized)
        return normalized

    async def remove_blacklist(self, name: str) -> bool:
        return await self._db.remove_blacklist(name.strip())

    async def is_blacklisted(self, chat_title: str | None, chat_username: str | None) -> bool:
        """Check if chat title or username matches any blacklisted name."""
        blacklist = await self._db.list_blacklist()
        for entry in blacklist:
            entry_lower = entry.lower()
            if chat_title and chat_title.lower() == entry_lower:
                return True
            if chat_username and chat_username.lower() == entry_lower:
                return True
        return False

    async def list_blacklist(self) -> list[str]:
        return await self._db.list_blacklist()

    def scan_message(
        self,
        text: str,
        chat_id: int,
        chat_title: str | None,
        message_id: int,
        sender_name: str | None,
        sender_username: str | None,
        is_edit: bool,
        chat_username: str | None,
        keywords: list[str],
    ) -> str | None:
        """
        Scan text against provided keywords.
        Returns formatted notification text, or None if no matches.
        """
        if not keywords:
            return None

        matched_keywords: list[str] = []
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                matched_keywords.append(kw)

        if not matched_keywords:
            return None

        message_link = self.build_message_link(chat_id, message_id, chat_username)
        snippet = text[: self.config.snippet_length]
        if len(text) > self.config.snippet_length:
            snippet += "..."

        return self._format_notification(
            matched_keywords, chat_title, sender_name, sender_username,
            snippet, message_link, is_edit,
        )

    def build_message_link(
        self, chat_id: int, message_id: int, chat_username: str | None
    ) -> str | None:
        """
        Public groups/channels: https://t.me/{username}/{message_id}
        Private groups/channels: https://t.me/c/{chat_id}/{message_id} (strip -100 prefix)
        DMs (positive chat_id) and basic groups: None
        """
        if chat_id > 0:
            return None

        if chat_username:
            return f"https://t.me/{chat_username}/{message_id}"

        chat_id_str = str(chat_id)
        if chat_id_str.startswith("-100"):
            stripped_id = chat_id_str[4:]
            return f"https://t.me/c/{stripped_id}/{message_id}"

        return None

    def _format_notification(
        self,
        keywords: list[str],
        chat_title: str | None,
        sender_name: str | None,
        sender_username: str | None,
        snippet: str,
        message_link: str | None,
        is_edit: bool,
    ) -> str:
        keywords_str = ", ".join(f"**{kw}**" for kw in keywords)

        lines: list[str] = []
        if is_edit:
            lines.append("✏️ **Message edited**")
        lines.append(f"🔔 Keyword matched: {keywords_str}")
        lines.append("")

        if chat_title:
            lines.append(f"💬 Chat: {chat_title}")

        sender_parts: list[str] = []
        if sender_name:
            sender_parts.append(sender_name)
        if sender_username:
            sender_parts.append(f"@{sender_username}")
        if sender_parts:
            lines.append(f"👤 From: {' '.join(sender_parts)}")

        if snippet:
            lines.append(f'📝 "{snippet}"')

        if message_link:
            lines.append(f"🔗 {message_link}")

        return "\n".join(lines)
