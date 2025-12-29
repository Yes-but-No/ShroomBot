import json
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection

from shroom_bot import get_bot_config
from shroom_bot.game.models import Server, User

USER_DATA_FILE = Path("migration/users.json")
SERVER_DATA_FILE = Path("migration/servers.json")
SCHEMA_FILE = Path("shroom_bot/db/schema.sql")


def _datetime_converter(o: str | None) -> datetime | None:
    if o is None:
        return None
    return datetime.fromisoformat(o)


if __name__ == "__main__":
    config = get_bot_config()

    with USER_DATA_FILE.open("r", encoding="utf-8") as f:
        user_data = json.load(f)

    with SERVER_DATA_FILE.open("r", encoding="utf-8") as f:
        server_data = json.load(f)

    with Connection(config.sqlite_db_path) as conn:
        cursor = conn.cursor()

        schema_sql = SCHEMA_FILE.read_text()
        cursor.executescript(schema_sql)

        for user_entry in user_data:
            user = User(
                user_id=user_entry["user_id"],
                lifetime_farmed=user_entry["lifetime_farmed"],
                lifetime_tokens=user_entry["lifetime_tokens"],
                tokens=user_entry["tokens"],
                created_at=_datetime_converter(user_entry["created_at"]),
            )
            cursor.execute(
                """
                INSERT INTO users (user_id, lifetime_farmed, lifetime_tokens, tokens, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user.user_id,
                    user.lifetime_farmed,
                    user.lifetime_tokens,
                    user.tokens,
                    user.created_at,
                ),
            )

        for server_entry in server_data:
            server = Server(
                server_id=server_entry["server_id"],
                farm_channel_id=server_entry["farm_channel_id"],
                daily_goal=server_entry["daily_goal"],
                last_farmer_id=server_entry["last_farmer_id"],
                lifetime_farmed=server_entry["lifetime_farmed"],
                best_daily=server_entry["best_daily"],
                best_weekly=server_entry["best_weekly"],
            )
            cursor.execute(
                """
                INSERT INTO servers (server_id, farm_channel_id, daily_goal, last_farmer_id, lifetime_farmed, best_daily, best_weekly)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    server.server_id,
                    server.farm_channel_id,
                    server.daily_goal,
                    server.last_farmer_id,
                    server.lifetime_farmed,
                    server.best_daily,
                    server.best_weekly,
                ),
            )

        conn.commit()
