from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from discord import Colour, Embed

if TYPE_CHECKING:
    from .game.ranks import RankInfo


def farm_already_exists() -> Embed:
    return Embed(
        title="Farm already exists!",
        description="Your server already has a farm set up, if you wish to change the farm channel, use `/setchannel` instead",
        colour=Colour.red(),
    )


def change_farm_channel_not_set_up() -> Embed:
    return Embed(
        title="Farm not set up!",
        description="Your server has not set up the farm yet, use `/farm setup` instead",
        colour=Colour.red(),
    )


def farm_not_set_up() -> Embed:
    return Embed(
        title="Farm not set up!",
        description="Use `/farm setup` to setup your server and start farming!",
        colour=Colour.red(),
    )


def account_not_found() -> Embed:
    return Embed(
        title="Account not found!",
        description="User has not started farming yet",
        colour=Colour.red(),
    )


def cannot_farm() -> Embed:
    return Embed(
        title="You cannot farm mushrooms now",
        description="You can only farm mushrooms one at a time",
        colour=Colour.red(),
    )


def daily_goal_reached() -> Embed:
    return Embed(
        title="Daily goal reached!",
        description="All contributors have been awarded double Shroom Tokens!",
        colour=Colour.green(),
    )


def under_maintenance() -> Embed:
    return Embed(
        title="Bot is under maintenance",
        description="Bot is currently under maintenance, please try again later",
        colour=Colour.red(),
    )


def farm_create_success(channel_id: int) -> Embed:
    return Embed(
        title="Success!",
        description=f"Farm created successfully, send a 🍄 in <#{channel_id}> to start farming!",
        colour=Colour.green(),
    )


def channel_change_success(channel_id: int) -> Embed:
    return Embed(
        title="Success!",
        description=f"The farm channel has been successfully changed to <#{channel_id}>",
        colour=Colour.green(),
    )


def set_daily_goal_success(goal: int) -> Embed:
    return Embed(
        title="Success!",
        description=(
            f"The daily goal has been successfully changed to `{goal}`\n"
            "If you have already farmed mushrooms today, the daily goal will only apply tomorrow!"
        ),
        colour=Colour.green(),
    )


def error_message(message: str) -> Embed:
    return Embed(
        title="Error",
        description=message,
        colour=Colour.red(),
    )


def user_ranked_up(new_rank: str) -> Embed:
    return Embed(
        title="Ranked up!",
        description=f"Your rank is now `{new_rank}`!",
        colour=Colour.green(),
    )


def coming_back_soon() -> Embed:
    return Embed(
        title="Coming back soon!",
        description="This feature is coming back soon, stay tuned!",
        colour=Colour.blue(),
    )


def farm_stats(
    server_name: str,
    farmed_today: int,
    farmed_this_week: int,
    farmed_ever: int,
    daily_goal: int | None,
    farm_channel_id: int,
    last_farmer_id: int | None,
    best_daily: int,
    best_weekly: int,
) -> Embed:
    return (
        Embed(
            title=f"Farm Stats for {server_name}",
            timestamp=datetime.now(),
            colour=Colour.blue(),
        )
        .add_field(name="Farmed Today", value=farmed_today)
        .add_field(name="Farmed This Week", value=farmed_this_week)
        .add_field(name="Farmed Ever", value=farmed_ever)
        .add_field(name="Daily Goal", value=daily_goal if daily_goal else "Not Set")
        .add_field(name="Farm Channel", value=f"<#{farm_channel_id}>")
        .add_field(
            name="Last Farmer",
            value=f"<@{last_farmer_id}>" if last_farmer_id else "No one yet",
        )
        .add_field(name="Most Farmed in a Day", value=best_daily)
        .add_field(name="Most Farmed in a Week", value=best_weekly)
    )


def user_stats(
    user_name: str,
    user_created_at: datetime,
    user_rank_info: RankInfo,
    tokens: int,
    farmed_today: int,
    farmed_this_week: int,
    farmed_ever: int,
) -> Embed:
    return (
        Embed(
            title=f"Farm Stats for {user_name}",
            timestamp=user_created_at.replace(tzinfo=UTC),
            colour=Colour.blue(),
        )
        .add_field(name="Rank", value=user_rank_info.current_rank.name)
        .add_field(
            name="Next Rank Requirement",
            value=f"{user_rank_info.next_rank.requirement} mushrooms"
            if user_rank_info.next_rank
            else "Max Rank!",
        )
        .add_field(name="Shroom Tokens", value=tokens)
        .add_field(name="Farmed Today", value=farmed_today)
        .add_field(name="Farmed This Week", value=farmed_this_week)
        .add_field(name="Farmed Ever", value=farmed_ever)
        .set_footer(text="Started farming on")
    )
