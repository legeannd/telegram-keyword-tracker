"""SQLite database for keyword persistence."""

from __future__ import annotations

import aiosqlite


class Database:
    def __init__(self, path: str) -> None:
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self._path)
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT NOT NULL UNIQUE COLLATE NOCASE
            )
            """
        )
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            )
            """
        )
        await self._db.commit()

    async def add_keyword(self, phrase: str) -> None:
        assert self._db is not None
        await self._db.execute("INSERT INTO keywords (phrase) VALUES (?)", (phrase,))
        await self._db.commit()

    async def remove_keyword(self, phrase: str) -> bool:
        assert self._db is not None
        cursor = await self._db.execute(
            "DELETE FROM keywords WHERE phrase = ? COLLATE NOCASE", (phrase,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def list_keywords(self) -> list[str]:
        assert self._db is not None
        cursor = await self._db.execute("SELECT phrase FROM keywords ORDER BY id")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def add_blacklist(self, name: str) -> None:
        assert self._db is not None
        await self._db.execute(
            "INSERT INTO blacklist (name) VALUES (?)", (name,)
        )
        await self._db.commit()

    async def remove_blacklist(self, name: str) -> bool:
        assert self._db is not None
        cursor = await self._db.execute(
            "DELETE FROM blacklist WHERE name = ? COLLATE NOCASE", (name,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def list_blacklist(self) -> list[str]:
        assert self._db is not None
        cursor = await self._db.execute("SELECT name FROM blacklist ORDER BY id")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def close(self) -> None:
        if self._db:
            await self._db.close()
