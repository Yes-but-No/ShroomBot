from __future__ import annotations

import asyncio
import datetime
import os
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from shroom import ShroomFarm
from utils import int_to_ordinal

if TYPE_CHECKING:
  from discord import Message

DEV_SERVER = discord.Object(id=os.getenv("DEV_SERVER_ID")) # type: ignore
SHROOM_RESET_TIME = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)



class ShroomBot(commands.Bot):
  def __init__(self, *args, **kwargs):
    self.shroom_farm = ShroomFarm()
    self._lock = asyncio.Lock()
    self.presence_selector = True
    super().__init__(*args, **kwargs)

  @tasks.loop(time=SHROOM_RESET_TIME)
  async def update_stats_loop(self):
    async with self._lock:
      await self.shroom_farm.update_daily_stats()

  @tasks.loop(minutes=1)
  async def update_presence_loop(self):
    if self.presence_selector:
      n = await self.shroom_farm.get_total_weekly_farmed() # technically we could just cache this and just add total to it
      msg = f"{n} mushrooms farmed this week"              # but I'm too lazy
    else:
      n = self.shroom_farm.daily_stats.total
      msg = f"{n} mushrooms farmed today"
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

    self.tree.copy_global_to(guild=DEV_SERVER)
    await self.tree.sync(guild=DEV_SERVER)

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
      await context.reply(
        embed=discord.Embed(
          title="Error!",
          description=str(exception),
          colour=discord.Colour.red()
        )
      )
    else:
      return await super().on_command_error(context, exception)

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
        embed = discord.Embed(
          title="You cannot farm mushrooms now",
          description="You can only farm mushrooms one at a time",
          colour=discord.Colour.red()
        )
      else:
        result = await self.shroom_farm.farm(farm, message.author.id) # type: ignore
        await message.add_reaction("🍄")

        farm_stats = result["farm_stats"]

        embeds = []

        embed = discord.Embed(
          title="Mushroom farmed!",
          description=f"{int_to_ordinal(farm_stats.farmed)} mushroom farmed today!",
          colour=discord.Colour.green()
        )
        # If we have not reached daily goal, show how many more to the daily goal
        if (
          not farm_stats.daily_goal_reached
          and farm_stats.daily_goal is not None
        ):
          embed.description += f"\n{farm_stats.daily_goal-farm_stats.farmed} more mushrooms till the daily goal!" # type: ignore
        
        embeds.append(embed)

        # Check if server has reached daily goal
        if all((
          farm_stats.daily_goal is not None,
          farm_stats.daily_goal_reached,
          not farm_stats.awarded_daily
        )):
          await self.shroom_farm.award_contributors(farm_stats)
          embeds.append(
            discord.Embed(
              title="Daily goal reached!",
              description="All contributors have been awarded double Shroom Tokens!",
              colour=discord.Colour.green()
            )
          )

        # Check if user has ranked up
        user = result["user"]
        if user.ranked_up:
          await self.shroom_farm.rank_up_user(user._id)
          embeds.append(
            discord.Embed(
              title=f"{message.author.name} ranked up!",
              description=f"Your rank is now `{user.next_rank.name}`!", # type: ignore
              colour=discord.Colour.green()
            )
          )
        
        return await message.reply(embeds=embeds)
      await message.reply(embed=embed)
    else:
      await self.process_commands(message)