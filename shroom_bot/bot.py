from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Self

import discord
from discord import app_commands
from discord.ext import commands, tasks

from . import embeds
from .config import BotConfig, constants
from .db import Database
from .errors import UnderMaintenance
from .game import Game
from .utils import int_to_ordinal

if TYPE_CHECKING:
    from .game.models import Server


BOT_TIMEZONE = datetime.timezone(datetime.timedelta(hours=8))  # UTC+8
# Bot reset time should at midnight local time (UTC+8)
BOT_RESET_TIME = datetime.time(hour=0, minute=0, tzinfo=BOT_TIMEZONE)

_logger = logging.getLogger(__name__)


class ShroomBot(commands.Bot):
    def __init__(self, config: BotConfig, *args, **kwargs):
        self.config = config

        self.dev_server: discord.Object = discord.Object(config.dev_server_id)
        self.token = config.token
        self.prefix = config.prefix
        self.maintenance_mode = config.maintenance_mode

        self.database = Database(config.sqlite_db_path)

        self.game = Game(self.database)

        self.presence_selector = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.prefix), *args, **kwargs
        )

        self.add_check(self.global_command_check)

        self.default_tree_on_error = (
            self.tree.on_error
        )  # this needs to be after __init__ since it is created in there
        self.tree.error(self.on_tree_error)

    @property
    def under_maintenance(self) -> bool:
        return self.maintenance_mode

    async def global_command_check(self, ctx: commands.Context) -> bool:
        if not await self.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot.")
        return True

    def run(self, *args, **kwargs):
        super().run(self.token, *args, **kwargs)

    @tasks.loop(time=BOT_RESET_TIME)
    async def daily_reset_loop(self):
        _logger.info("Cleaning up daily stats...")
        await self.game.cleanup_old_stats(self.get_stats_date(), max_age_days=31)

    @tasks.loop(minutes=1)
    async def update_presence_loop(self):
        if self.under_maintenance:
            await self.change_presence(
                activity=discord.Game(name="Under Maintenance"),
                status=discord.Status.idle,
            )
            return

        _stats_date = self.get_stats_date()
        if self.presence_selector:
            _week_start = _stats_date - datetime.timedelta(days=_stats_date.weekday())
            _week_end = _week_start + datetime.timedelta(days=6)
            farmed_this_week = await self.game.get_global_timespan_farmed(
                _week_start, _week_end
            )
            msg = f"{farmed_this_week} mushroom farmed this week!"
        else:
            farmed_today = await self.game.get_global_daily_farmed(_stats_date)
            msg = f"{farmed_today} mushroom farmed today!"
        self.presence_selector = not self.presence_selector
        await self.change_presence(
            activity=discord.Game(name=msg), status=discord.Status.online
        )

    @update_presence_loop.before_loop
    async def before_update_presence_loop(self):
        await self.wait_until_ready()

    async def _cleanup_unused_locks(self):
        self.game.cleanup_server_locks(self.config.lock_timeout)

    async def setup_hook(self) -> None:
        await self.database.connect()
        await self.database.init_schema()

        self.daily_reset_loop.start()
        self.update_presence_loop.start()

        self.cleanup_unused_locks_loop = tasks.loop(
            seconds=self.config.lock_cleanup_interval_seconds
        )(self._cleanup_unused_locks)
        self.cleanup_unused_locks_loop.start()

        for ext in constants.EXTENSIONS:
            _logger.info(f"Loading extension: {ext}")
            try:
                await self.load_extension(ext)
            except Exception as e:
                _logger.error(f"Failed to load extension {ext}: {e}")

    async def close(self) -> None:
        await self.database.close()
        await super().close()

    async def on_tree_error(
        self,
        interaction: discord.Interaction[Self],
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, UnderMaintenance):
            await interaction.response.send_message(embed=embeds.under_maintenance())
            return

        if isinstance(error, app_commands.MissingPermissions):
            msg = "You do not have the required permissions to run this command"
        else:
            msg = "An unknown error has occurred"
            _logger.error(f"An error occurred: {error}", exc_info=error)
            await self.default_tree_on_error(interaction, error)
        await interaction.response.send_message(embed=embeds.error_message(msg))

    async def on_command_error(
        self, context: commands.Context, exception: commands.CommandError
    ) -> None:
        if isinstance(
            exception,
            commands.UserInputError
            | commands.CheckFailure
            | commands.CommandNotFound
            | app_commands.MissingPermissions,
        ):
            msg = str(exception)
        else:
            msg = "An unknown error has occurred"
            _logger.error(f"An error occurred: {exception}", exc_info=exception)
            await super().on_command_error(context, exception)

        try:
            await context.reply(embed=embeds.error_message(msg))
        except Exception as e:
            _logger.error(f"Failed to send error message: {e}", exc_info=e)

    def get_stats_date(self, now: datetime.datetime | None = None) -> datetime.date:
        if now is None:
            now = datetime.datetime.now(tz=BOT_TIMEZONE)
        else:
            now = now.astimezone(BOT_TIMEZONE)

        return now.date()

    async def farm(
        self,
        server: Server,
        message: discord.Message,
        user_id: int | None = None,
        amount: int = 1,
        ignore_last: bool = False,
    ) -> None:
        async with self.game.acquire_server_lock(server.server_id):
            user_id = user_id or message.author.id

            if not ignore_last and server.last_farmer_id == user_id:
                try:
                    await message.add_reaction("❌")
                    await message.reply(
                        embed=embeds.cannot_farm(), mention_author=False
                    )
                except discord.NotFound:
                    await message.channel.send(
                        message.author.mention, embed=embeds.cannot_farm(), silent=True
                    )
                return

            result = await self.game.farm_mushrooms(
                server,
                user_id,
                self.get_stats_date(),
                amount,
            )
            await self.game.commit()

            _embeds = []
            _embed = discord.Embed(
                title="Mushroom Farmed!",
                description=f"{int_to_ordinal(result.daily_count)} mushroom farmed today!",
                colour=discord.Colour.green(),
            )

            # If daily goal not reached, show progress towards goal
            if server.daily_goal > 0 and not result.daily_goal_reached:
                _embed.description += f"\n{result.daily_goal - result.daily_count} more mushrooms till the daily goal!"  # type: ignore

            _embeds.append(_embed)

            # Check if daily goal was reached with this farm
            if result.daily_goal_reached and result.awarding_daily_bonus:
                goal_embed = embeds.daily_goal_reached()
                _embeds.append(goal_embed)

            if result.user_ranked_up:
                rank_embed = embeds.user_ranked_up(result.user_rank_name)
                _embeds.append(rank_embed)

            try:
                await message.add_reaction("🍄")
                for embed in _embeds:
                    await message.reply(embed=embed, mention_author=False)
            except discord.NotFound:
                for embed in _embeds:
                    await message.channel.send(
                        message.author.mention, embed=embed, silent=True
                    )

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.content == "🍄":
            if message.guild is None:
                return
            server = await self.game.get_server(message.guild.id)
            if server is None or server.farm_channel_id is None:
                _embed = embeds.farm_not_set_up()
            elif server.farm_channel_id != message.channel.id:
                return
            elif self.under_maintenance:
                _embed = embeds.under_maintenance()
            else:
                await self.farm(server, message)
                return

            try:
                await message.reply(embed=_embed, mention_author=False)
            except discord.NotFound:
                await message.channel.send(
                    message.author.mention, embed=_embed, silent=True
                )
        else:
            await self.process_commands(message)
