from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from attrs import define, field

from ._utils import get_env

_logger = logging.getLogger(__name__)


@define
class BotConfig:
    token: str = field(factory=get_env("TOKEN", ""))
    dev_server_id: int = field(factory=get_env("DEV_SERVER_ID", 0))
    prefix: str = field(factory=get_env("PREFIX", "$"))
    maintenance_mode: bool = field(factory=get_env("MAINTENANCE_MODE", False))
    lock_cleanup_interval_seconds: int = field(
        factory=get_env("LOCK_CLEANUP_INTERVAL", 60)
    )
    lock_timeout: int = field(factory=get_env("LOCK_TIMEOUT", 60))
    sqlite_db_path: Path = field(
        factory=get_env("SQLITE_DB_PATH", Path("shroom_bot.db"))
    )

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> BotConfig:
        env_file = Path(f"{os.curdir}/{dotenv_filename}")

        if env_file.exists():
            from dotenv import load_dotenv

            _logger.info(f"Loading environment configuration from {dotenv_filename}")

            load_dotenv(dotenv_path=env_file, override=True)
        return cls()


@lru_cache(maxsize=1, typed=True)
def get_bot_config() -> BotConfig:
    return BotConfig.from_env()
