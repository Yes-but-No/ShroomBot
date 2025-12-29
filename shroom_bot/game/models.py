from __future__ import annotations

from datetime import date, datetime

from attrs import define


@define(slots=True)
class User:
    user_id: int

    lifetime_farmed: int = 0
    lifetime_tokens: int = 0
    tokens: int = 0

    last_farmed_at: datetime | None = None
    created_at: datetime | None = None


@define(slots=True)
class Server:
    server_id: int
    farm_channel_id: int

    daily_goal: int = 0
    last_farmer_id: int | None = None

    lifetime_farmed: int = 0
    best_daily: int = 0
    best_weekly: int = 0

    created_at: datetime | None = None


@define(slots=True)
class DailyServerStats:
    server_id: int
    stat_date: date

    daily_count: int = 0
    goal_reached: bool = False
    goal_snapshot: int = 0


@define(slots=True)
class DailyUserStats:
    server_id: int
    user_id: int
    stat_date: date

    farmed: int = 0
