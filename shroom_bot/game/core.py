from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta

from attrs import define

from ..db import Database
from .models import DailyServerStats, DailyUserStats, Server, User
from .ranks import get_rank_info

_logger = logging.getLogger(__name__)


@define
class ServerLock:
    lock: asyncio.Lock
    active: int = 0
    last_used: float = 0.0


@define
class FarmResult:
    daily_count: int
    daily_goal_reached: bool
    daily_goal: int
    user_rank_name: str
    user_ranked_up: bool = False
    awarding_daily_bonus: bool = False


class Game:
    def __init__(self, db: Database):
        self.db = db
        self._server_locks: dict[int, ServerLock] = {}  # server_id -> ServerLock

    # ----------------------------------------------------------------
    # COMMIT UTILS
    # ----------------------------------------------------------------

    async def commit(self) -> None:
        await self.db.conn.commit()

    @asynccontextmanager
    async def autosave(self):
        # We don't use a try/finally here because if an exception occurs, we want it to propagate
        yield
        await self.db.conn.commit()

    # ----------------------------------------------------------------
    # LOCKS
    # ----------------------------------------------------------------

    @asynccontextmanager
    async def acquire_server_lock(self, server_id: int):
        """Acquire a lock for a specific server."""
        if server_id not in self._server_locks:
            self._server_locks[server_id] = ServerLock(lock=asyncio.Lock())

        server_lock = self._server_locks[server_id]
        server_lock.active += 1
        server_lock.last_used = time.monotonic()

        try:
            async with server_lock.lock:
                yield
        finally:
            server_lock.active -= 1
            server_lock.last_used = time.monotonic()

    def cleanup_server_locks(self, threshold_seconds: float | int):
        """Cleanup server locks that have been inactive for a certain threshold."""
        current_time = time.monotonic()
        to_remove = [
            server_id
            for server_id, server_lock in self._server_locks.items()
            if server_lock.active == 0
            and (current_time - server_lock.last_used) > threshold_seconds
        ]

        for server_id in to_remove:
            del self._server_locks[server_id]
            _logger.info(f"Cleaned up unused lock for server_id={server_id}")

    # ----------------------------------------------------------------
    # SERVER
    # ----------------------------------------------------------------

    async def create_server(
        self, server_id: int, farm_channel_id: int | None = None
    ) -> bool:
        cursor = await self.db.conn.execute(
            "INSERT OR IGNORE INTO servers (server_id, farm_channel_id) VALUES (?, ?)",
            (server_id, farm_channel_id),
        )
        return cursor.rowcount > 0

    async def get_server(self, server_id: int) -> Server | None:
        cursor = await self.db.conn.execute(
            "SELECT * FROM servers WHERE server_id = ?", (server_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Server(**row)

    async def save_server(self, server: Server) -> bool:
        cursor = await self.db.conn.execute(
            """
            UPDATE servers
            SET farm_channel_id = ?,
                daily_goal = ?,
                last_farmer_id = ?,
                lifetime_farmed = ?,
                best_daily = ?,
                best_weekly = ?
            WHERE server_id = ?
            """,
            (
                server.farm_channel_id,
                server.daily_goal,
                server.last_farmer_id,
                server.lifetime_farmed,
                server.best_daily,
                server.best_weekly,
                server.server_id,
            ),
        )
        return cursor.rowcount > 0

    async def set_farm_channel(self, server_id: int, farm_channel_id: int) -> bool:
        cursor = await self.db.conn.execute(
            "UPDATE servers SET farm_channel_id = ? WHERE server_id = ?",
            (farm_channel_id, server_id),
        )
        return cursor.rowcount > 0

    async def set_server_daily_goal(self, server_id: int, daily_goal: int) -> bool:
        cursor = await self.db.conn.execute(
            "UPDATE servers SET daily_goal = ? WHERE server_id = ?",
            (daily_goal, server_id),
        )
        return cursor.rowcount > 0

    # ----------------------------------------------------------------
    # USERS
    # ----------------------------------------------------------------

    async def ensure_user_exists(self, user_id: int) -> None:
        await self.db.conn.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )

    async def get_user(self, user_id: int) -> User | None:
        cursor = await self.db.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return User(**row)

    async def save_user(self, user: User) -> bool:
        cursor = await self.db.conn.execute(
            """
            UPDATE users
            SET lifetime_farmed = ?,
                lifetime_tokens = ?,
                tokens = ?,
                last_farmed_at = ?
            WHERE user_id = ?
            """,
            (
                user.lifetime_farmed,
                user.lifetime_tokens,
                user.tokens,
                user.last_farmed_at,
                user.user_id,
            ),
        )
        return cursor.rowcount > 0

    async def increment_user_farmed(self, user_id: int, amount: int = 1) -> bool:
        cursor = await self.db.conn.execute(
            """
            UPDATE users
            SET lifetime_farmed = lifetime_farmed + ?,
                last_farmed_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (amount, user_id),
        )
        return cursor.rowcount > 0

    async def increment_user_tokens(self, user_id: int, amount: int = 1) -> bool:
        cursor = await self.db.conn.execute(
            """
            UPDATE users
            SET lifetime_tokens = lifetime_tokens + ?,
                tokens = tokens + ?
            WHERE user_id = ?
            """,
            (amount, amount, user_id),
        )
        return cursor.rowcount > 0

    # ----------------------------------------------------------------
    # SERVER STATS
    # ----------------------------------------------------------------

    async def ensure_daily_server_stats_exists(
        self, server: Server, stat_date: date
    ) -> None:
        # REMEMBER TO MANUALLY COMMIT AFTER CALLING THIS METHOD
        await self.db.conn.execute(
            """
            INSERT OR IGNORE INTO daily_server_stats (server_id, stat_date, goal_snapshot)
            VALUES (?, ?, ?)
            """,
            (server.server_id, stat_date, server.daily_goal),
        )

    async def get_daily_server_stats(
        self, server_id: int, stat_date: date
    ) -> DailyServerStats | None:
        cursor = await self.db.conn.execute(
            """
            SELECT * FROM daily_server_stats
            WHERE server_id = ? AND stat_date = ?
            """,
            (server_id, stat_date),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return DailyServerStats(**row)

    async def get_server_timespan_farmed(
        self, server_id: int, start_date: date, end_date: date
    ) -> int:
        cursor = await self.db.conn.execute(
            """
            SELECT SUM(daily_count) as total_farmed FROM daily_server_stats
            WHERE server_id = ? AND stat_date BETWEEN ? AND ?
            """,
            (server_id, start_date, end_date),
        )
        row = await cursor.fetchone()
        if row is None or row["total_farmed"] is None:
            return 0
        return row["total_farmed"]

    async def save_daily_server_stats(self, stats: DailyServerStats) -> bool:
        cursor = await self.db.conn.execute(
            """
            UPDATE daily_server_stats
            SET daily_count = ?,
                goal_snapshot = ?,
                goal_reached = ?
            WHERE server_id = ? AND stat_date = ?
            """,
            (
                stats.daily_count,
                stats.goal_snapshot,
                stats.goal_reached,
                stats.server_id,
                stats.stat_date,
            ),
        )
        return cursor.rowcount > 0

    # ----------------------------------------------------------------
    # USER STATS
    # ----------------------------------------------------------------

    async def get_daily_user_stats(
        self, server_id: int, user_id: int, stat_date: date
    ) -> DailyUserStats | None:
        cursor = await self.db.conn.execute(
            """
            SELECT * FROM daily_user_stats
            WHERE server_id = ? AND user_id = ? AND stat_date = ?
            """,
            (server_id, user_id, stat_date),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return DailyUserStats(**row)

    async def increment_daily_user_farmed(
        self, server_id: int, user_id: int, stat_date: date, amount: int = 1
    ) -> bool:
        cursor = await self.db.conn.execute(
            """
            INSERT INTO daily_user_stats (server_id, user_id, stat_date, farmed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(server_id, user_id, stat_date)
            DO UPDATE SET farmed = farmed + ?
            """,
            (server_id, user_id, stat_date, amount, amount),
        )
        return cursor.rowcount > 0

    async def get_daily_users_by_server_id(
        self, server_id: int, stat_date: date
    ) -> list[DailyUserStats]:
        cursor = await self.db.conn.execute(
            """
            SELECT * FROM daily_user_stats
            WHERE server_id = ? AND stat_date = ?
            """,
            (server_id, stat_date),
        )
        rows = await cursor.fetchall()
        return [DailyUserStats(**row) for row in rows]

    async def get_user_timespan_farmed(
        self, server_id: int, user_id: int, start_date: date, end_date: date
    ) -> int:
        cursor = await self.db.conn.execute(
            """
            SELECT SUM(farmed) as total_farmed FROM daily_user_stats
            WHERE server_id = ? AND user_id = ? AND stat_date BETWEEN ? AND ?
            """,
            (server_id, user_id, start_date, end_date),
        )
        row = await cursor.fetchone()
        if row is None or row["total_farmed"] is None:
            return 0
        return row["total_farmed"]

    # ----------------------------------------------------------------
    # GLOBAL STATS
    # ----------------------------------------------------------------

    async def get_global_daily_farmed(self, stat_date: date) -> int:
        cursor = await self.db.conn.execute(
            """
            SELECT SUM(farmed) as total_farmed FROM daily_user_stats
            WHERE stat_date = ?
            """,
            (stat_date,),
        )
        row = await cursor.fetchone()
        if row is None or row["total_farmed"] is None:
            return 0
        return row["total_farmed"]

    async def get_global_timespan_farmed(self, start_date: date, end_date: date) -> int:
        cursor = await self.db.conn.execute(
            """
            SELECT SUM(farmed) as total_farmed FROM daily_user_stats
            WHERE stat_date BETWEEN ? AND ?
            """,
            (start_date, end_date),
        )
        row = await cursor.fetchone()
        if row is None or row["total_farmed"] is None:
            return 0
        return row["total_farmed"]

    # ----------------------------------------------------------------
    # FARMING OPERATIONS
    # ----------------------------------------------------------------

    async def award_daily_bonus(self, server_stats: DailyServerStats):
        contributors = await self.get_daily_users_by_server_id(
            server_stats.server_id, server_stats.stat_date
        )

        for contributor in contributors:
            # Award double tokens for daily goal achievement
            await self.increment_user_tokens(contributor.user_id, contributor.farmed)

    async def farm_mushrooms(
        self, server: Server, user_id: int, stat_date: date, amount: int = 1
    ) -> FarmResult:
        _logger.info(
            f"Farming {amount} mushrooms for user_id={user_id} on server_id={server.server_id} for date={stat_date}"
        )
        await self.ensure_user_exists(user_id)
        await self.ensure_daily_server_stats_exists(server, stat_date)

        # Increment user daily count
        await self.increment_daily_user_farmed(
            server.server_id, user_id, stat_date, amount
        )

        # Increment server daily count
        cursor = await self.db.conn.execute(
            """
            UPDATE daily_server_stats
            SET daily_count = daily_count + ?
            WHERE server_id = ? AND stat_date = ?
            RETURNING *
            """,
            (amount, server.server_id, stat_date),
        )
        row = await cursor.fetchone()
        server_stats = DailyServerStats(**row)  # type: ignore

        # Update server lifetime farmed
        server.lifetime_farmed += amount
        server.last_farmer_id = user_id

        # Check if server daily record is beaten
        if server_stats.daily_count > server.best_daily:
            server.best_daily = server_stats.daily_count

        # Check if server weekly record is beaten
        week_start = stat_date - timedelta(days=stat_date.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_farmed = await self.get_server_timespan_farmed(
            server.server_id, week_start, week_end
        )
        if weekly_farmed > server.best_weekly:
            server.best_weekly = weekly_farmed

        user = await self.get_user(user_id)
        assert user is not None  # Should never be None due to ensure_user_exists
        user_rank_info = get_rank_info(user.lifetime_farmed)
        user_rank_name = user_rank_info.current_rank.name
        user_ranked_up = False

        # Update user stats
        user.lifetime_farmed += amount
        user.tokens += amount  # 1 token per mushroom farmed
        user.lifetime_tokens += amount
        user.last_farmed_at = datetime.now(UTC)

        # Save changes
        await self.save_user(user)
        await self.save_server(server)

        # Check for rank up
        if (
            user_rank_info.next_rank is not None
            and user.lifetime_farmed >= user_rank_info.next_rank.requirement
        ):
            user_ranked_up = True
            # User might somehow rank up multiple times at once
            new_rank_info = get_rank_info(user.lifetime_farmed)
            user_rank_name = new_rank_info.current_rank.name

        # Check if daily goal is reached
        if (
            not server_stats.goal_reached
            and server_stats.daily_count >= server_stats.goal_snapshot > 0
        ):
            server_stats.goal_reached = True
            awarding_daily_bonus = True
            await self.db.conn.execute(
                """
                UPDATE daily_server_stats
                SET goal_reached = 1
                WHERE server_id = ? AND stat_date = ?
                """,
                (server.server_id, stat_date),
            )
            await self.award_daily_bonus(server_stats)
        else:
            awarding_daily_bonus = False

        return FarmResult(
            daily_count=server_stats.daily_count,
            daily_goal_reached=server_stats.goal_reached,
            daily_goal=server_stats.goal_snapshot,
            user_rank_name=user_rank_name,
            user_ranked_up=user_ranked_up,
            awarding_daily_bonus=awarding_daily_bonus,
        )

    # ----------------------------------------------------------------
    # STAT CLEANUP OPERATIONS
    # ----------------------------------------------------------------

    async def cleanup_old_stats(self, stat_date: date, max_age_days: int) -> None:
        cutoff_date = stat_date - timedelta(days=max_age_days)

        await self.db.conn.execute(
            "DELETE FROM daily_server_stats WHERE stat_date < ?",
            (cutoff_date,),
        )

        await self.db.conn.execute(
            "DELETE FROM daily_user_stats WHERE stat_date < ?",
            (cutoff_date,),
        )
