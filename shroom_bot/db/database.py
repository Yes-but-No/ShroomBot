from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import aiosqlite

_logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        _logger.info(f"Connecting to database at {self.db_path}...")
        self._conn = await aiosqlite.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES
        )
        self._conn.row_factory = aiosqlite.Row

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database connection is not established.")
        return self._conn

    async def init_schema(self) -> None:
        _logger.info("Initializing database schema...")
        schema = Path(__file__).with_name("schema.sql").read_text()
        await self.conn.executescript(schema)
        await self.conn.commit()
