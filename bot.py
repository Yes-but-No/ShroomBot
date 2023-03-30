from __future__ import annotations

import asyncio
import datetime
import os
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from shroom import ShroomFarm

if TYPE_CHECKING:
  from discord import Message

DEV_SERVER = discord.Object(id=os.getenv("DEV_SERVER_ID")) # type: ignore
SHROOM_RESET_TIME = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)

def int_to_ordinal(n: int) -> str:
  s = str(n)
  if len(s) == 2 and s[0] == "1":
    s += "th"
  elif s[-1] == "1":
    s += "st"
  elif s[-1] == "2":
    s += "nd"
  elif s[-1] == "3":
    s += "rd"
  else:
    s += "th"
  return s



class ShroomBot(commands.Bot):
  def __init__(self, *args, **kwargs):
    self.shroom_farm = ShroomFarm()
    self.owner_ids = (751768586699276342, 759195783597129760)
    self._lock = asyncio.Lock()
    super().__init__(*args, **kwargs)

  @tasks.loop(time=SHROOM_RESET_TIME)
  async def update_stats_loop(self):
    async with self._lock:
      await self.shroom_farm.update_daily_stats()

  async def setup_hook(self) -> None:
    await self.shroom_farm.setup()

    # This might be a problem if the bot is started at exactly
    # 12am which could make an empty `DailyStats` object be inserted
    # into the database, but I'm sure it's fine...
    await self.update_stats_loop.start()

    self.tree.copy_global_to(guild=DEV_SERVER)
    await self.tree.sync(guild=DEV_SERVER)

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
        result = await self.shroom_farm.farm(message.guild.id, message.author.id) # type: ignore
        await message.add_reaction("🍄")

        farm_stats = result["farm_stats"]

        embeds = []
        embeds.append(
          discord.Embed(
            title="Mushroom farmed!",
            description=f"{int_to_ordinal(farm_stats.farmed)} mushroom farmed today!",
            colour=discord.Colour.green()
          )
        )

        # Check if server has reached daily goal
        if (
            farm_stats.daily_goal_reached
            and farm_stats.daily_goal is not None
            and not farm_stats.awarded_daily
          ):
          await self.shroom_farm.award_contributors(farm_stats)
          farm_stats.awarded_daily = True
          embeds.append(
            discord.Embed(
              title="Daily goal reached!",
              description="All contributors have been awarded double Shroom Tokens!"
            )
          )

        # Check if user has ranked up
        user = result["user"]
        if user.ranked_up:
          await self.shroom_farm.rank_up_user(user._id)
          embeds.append(
            discord.Embed(
              title=f"<@{user._id}> ranked up!",
              description=f"Your rank is now `{user.next_rank.name}`!" # type: ignore
            )
          )
        
        return await message.reply(embeds=embeds)
      await message.reply(embed=embed)
    else:
      await self.process_commands(message)