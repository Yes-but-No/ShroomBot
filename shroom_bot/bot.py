from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Self

import discord
from discord import app_commands
from discord.ext import commands, tasks

from . import embeds
from .config import BotConfig, constants
from .errors import UnderMaintenance
from .game import ShroomFarmGame
from .utils import int_to_ordinal

if TYPE_CHECKING:
    from .game.models import ShroomFarm


# 12am SGT -> 4pm UTC
SHROOM_RESET_TIME = datetime.time(hour=16, minute=0, tzinfo=datetime.UTC)

_logger = logging.getLogger(__name__)


class ShroomBot(commands.Bot):
    def __init__(self, config: BotConfig, *args, **kwargs):
        self.config = config

        self.dev_server: discord.Object = discord.Object(config.dev_server_id)
        self.token = config.token
        self.prefix = config.prefix
        self.maintenance_mode = config.maintenance_mode

        self.game = ShroomFarmGame()

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

    @tasks.loop(time=SHROOM_RESET_TIME)
    async def reset_daily_farmed_loop(self):
        _logger.info("Resetting daily farmed shrooms for all servers...")

        for farm_id in self.game._farms.keys():
            await self.game.acquire_farm_lock(farm_id)
            try:
                farm = await self.game.get_farm(farm_id)
                if farm is not None:
                    farm.farmed = 0
            except Exception as e:
                _logger.error(f"Failed to reset daily farmed for farm {farm_id}: {e}")
            finally:
                self.game.release_farm_lock(farm_id)

        _logger.info("Daily farmed shrooms reset complete!")

    @tasks.loop(minutes=1)
    async def update_presence_loop(self):
        if self.under_maintenance:
            await self.change_presence(
                activity=discord.Game(name="Under Maintenance"),
                status=discord.Status.idle,
            )
            return
        if self.presence_selector:
            await self.change_presence(
                activity=discord.Game(name="Farming Shrooms! 🍄"),
                status=discord.Status.online,
            )
        else:
            await self.change_presence(
                activity=discord.Game(name="in the forest! 🍄"),
                status=discord.Status.online,
            )
        self.presence_selector = not self.presence_selector

    @update_presence_loop.before_loop
    async def before_update_presence_loop(self):
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        self.reset_daily_farmed_loop.start()
        self.update_presence_loop.start()

        for ext in constants.EXTENSIONS:
            _logger.info(f"Loading extension: {ext}")
            try:
                await self.load_extension(ext)
            except Exception as e:
                _logger.error(f"Failed to load extension {ext}: {e}")

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

    async def farm(
        self,
        farm: ShroomFarm,
        message: discord.Message,
        user_id: int | None = None,
        amount: int = 1,
        ignore_last: bool = False,
    ) -> None:
        await self.game.acquire_farm_lock(farm.server_id)

        try:
            user_id = user_id or message.author.id

            if not ignore_last and farm.last_farmer_id == user_id:
                try:
                    await message.add_reaction("❌")
                    await message.reply(
                        embed=embeds.cannot_farm(), mention_author=False
                    )
                except discord.NotFound:
                    await message.channel.send(
                        message.author.mention, embed=embeds.cannot_farm(), silent=True
                    )
                finally:
                    self.game.release_farm_lock(farm.server_id)
                    return

            result = await self.game.update_server_farmed(
                farm.server_id, user_id, amount
            )

            _embed = discord.Embed(
                title="Mushrooms Farmed!",
                description=f"{int_to_ordinal(result.farmed)} mushroom farmed today!",
                colour=discord.Colour.green(),
            )

            try:
                await message.add_reaction("🍄")
                await message.reply(embed=_embed, mention_author=False)
            except discord.NotFound:
                await message.channel.send(
                    message.author.mention, embed=_embed, silent=True
                )

        finally:
            self.game.release_farm_lock(farm.server_id)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.content == "🍄":
            if message.guild is None:
                return
            farm = await self.game.get_farm(message.guild.id)
            if farm is None or farm.farm_channel_id is None:
                _embed = embeds.farm_not_set_up()
            elif farm.farm_channel_id != message.channel.id:
                return
            elif self.under_maintenance:
                _embed = embeds.under_maintenance()
            else:
                await self.farm(farm, message)
                return

            try:
                await message.reply(embed=_embed, mention_author=False)
            except discord.NotFound:
                await message.channel.send(
                    message.author.mention, embed=_embed, silent=True
                )
        else:
            await self.process_commands(message)
