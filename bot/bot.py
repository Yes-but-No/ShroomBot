from __future__ import annotations

import asyncio
import datetime
import logging
import os
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.cogs import COGS
from bot.shroom import ShroomFarm
from bot.utils import int_to_ordinal

if TYPE_CHECKING:
  from discord import Message

DEV_SERVER = discord.Object(id=os.getenv("DEV_SERVER_ID")) # type: ignore
SHROOM_RESET_TIME = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)

_log = logging.getLogger(__name__)



class ShroomBot(commands.Bot):
  def __init__(self, *args, **kwargs):
    url = kwargs.pop("mongo_url", "localhost")
    self.shroom_farm = ShroomFarm(url)
    self._lock = asyncio.Lock()
    self.presence_selector = True
    super().__init__(*args, **kwargs)
    
    self.default_tree_on_error = self.tree.on_error # this needs to be after __init__ since it is created in there
    self.tree.error(self.on_tree_error)


  @tasks.loop(time=SHROOM_RESET_TIME)
  async def update_stats_loop(self):
    async with self._lock:
      _log.info("Attempting to update daily stats")
      result = await self.shroom_farm.update_daily_stats()
      if result:
        _log.info("Daily Stats updated successfully")
      else:
        _log.warn("Daily Stats update was unsuccessful")

  @tasks.loop(minutes=1)
  async def update_presence_loop(self):
    if self.presence_selector:
      n = await self.shroom_farm.get_total_weekly_farmed() # technically we could just cache this and just add total to it
      msg = f"{n} farmed this week"                        # but I'm too lazy
    else:
      n = self.shroom_farm.daily_stats.total
      msg = f"{n} farmed today"
    self.presence_selector = not self.presence_selector
    await self.change_presence(activity=discord.Game(name=msg))

  @update_presence_loop.before_loop
  async def before_presence_loop(self):
    await self.wait_until_ready()

  async def setup_hook(self) -> None:
    await self.shroom_farm.setup()

    # This might be a problem if the bot is started at exactly
    # 12am which could make an empty `DailyStats` object be inserted
    # into the database, but I'm sure it's fine...
    self.update_stats_loop.start()
    self.update_presence_loop.start()

    for cog in COGS:
      _log.info(f"Loading cog `{cog!r}`")
      await self.add_cog(cog(self))

    self.tree.copy_global_to(guild=DEV_SERVER)
    await self.tree.sync(guild=DEV_SERVER)

    await self.tree.sync()

  async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
      msg = "You do not have the required permissions to run this command"
    else:
      msg = "An unknown error has occurred"
      await self.default_tree_on_error(interaction, error) # type: ignore
    await interaction.response.send_message(
      embed=discord.Embed(
        title="Error!",
        description=msg,
        colour=discord.Colour.red()
      )
    )
    

  async def on_command_error(self, context: commands.Context[ShroomBot], exception: commands.errors.CommandError, /) -> None:
    if isinstance(
      exception,
      (
        commands.UserInputError,
        commands.CheckFailure,
        commands.CommandNotFound,
        discord.app_commands.MissingPermissions
      )
    ):
      msg = str(exception)
    else:
      msg = "An unknown error has occurred"
      await super().on_command_error(context, exception)

    try:
      await context.reply(
        embed=discord.Embed(
          title="Error!",
          description=msg,
          colour=discord.Colour.red()
        )
      )
    except Exception: # It means we can't send a message so we ignore it
      pass

  async def on_message(self, message: Message):
    if message.author.bot:
      return

    if message.content == "🍄":
      if message.guild is None:
        return
      farm = await self.shroom_farm.get_farm(message.guild.id)
      if farm is None or farm.farm_channel is None:
        embed = discord.Embed(
          title="Farm not set up!",
          description="Use `/setup` to setup your server and start farming!",
          colour=discord.Colour.red()
        )
      elif farm.farm_channel != message.channel.id:
        return
      elif farm.last_farmer == message.author.id:
        await message.add_reaction("❌")
        embed = discord.Embed(
          title="You cannot farm mushrooms now",
          description="You can only farm mushrooms one at a time",
          colour=discord.Colour.red()
        )
      else:
        result = await self.shroom_farm.farm(farm, message.author.id)
        await message.add_reaction("🍄")

        embeds = []

        embed = discord.Embed(
          title="Mushroom farmed!",
          description=f"{int_to_ordinal(result.farmed)} mushroom farmed today!",
          colour=discord.Colour.green()
        )
        # If we have not reached daily goal, show how many more to the daily goal
        if (
          not result.daily_goal_reached
          and result.daily_goal is not None
        ):
          embed.description += f"\n{result.daily_goal-result.farmed} more mushrooms till the daily goal!" # type: ignore
        
        embeds.append(embed)

        # Check if server has reached daily goal
        if result.awarding_daily:
          embeds.append(
            discord.Embed(
              title="Daily goal reached!",
              description="All contributors have been awarded double Shroom Tokens!",
              colour=discord.Colour.green()
            )
          )
        if result.user_ranked_up:
          embeds.append(
            discord.Embed(
              title=f"{message.author.name} ranked up!",
              description=f"Your rank is now `{result.user.rank.name}`!",
              colour=discord.Colour.green()
            )
          )
        
        return await message.reply(embeds=embeds)
      await message.reply(embed=embed)
    else:
      await self.process_commands(message)
