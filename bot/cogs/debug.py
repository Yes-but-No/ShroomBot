from __future__ import annotations

import contextlib
import re
from io import StringIO
import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.embeds import FARM_ALREADY_EXISTS, FARM_CREATE_SUCCESS
from bot.utils import int_to_ordinal

if TYPE_CHECKING:
  from bot import ShroomBot

class Debug(commands.Cog):
  def __init__(self, bot: ShroomBot):
    self.bot = bot

  @property
  def cog_check(self):
    return commands.is_owner()
  

  @commands.command(hidden=True, aliases=["eval"])
  @commands.is_owner() # Just in case the cog_check didn't work properly
  async def exec(
    self,
    ctx: commands.Context,
    *,
    code: str
  ):
    line_break = "\n"

    code_block = re.findall(r"```([a-zA-Z0-9]*)\s([\s\S(^\\`{3})]*?)\s*```", code)
    code = code_block[0][1]

    sout = StringIO()
    serr = StringIO()
  
    with (
      contextlib.redirect_stdout(sout),
      contextlib.redirect_stderr(serr)
    ):
      try:
        func = (
          "async def exec_func(ctx, bot):\n"
          f"{line_break.join((' '*2 + line) for line in code.split(line_break))}"
        )
        exec(func, {"discord": discord})

        result = await locals()["exec_func"](ctx, self.bot)
      except BaseException as e:
        traceback.print_exc()
        result = type(e)

    sout, serr = sout.getvalue(), serr.getvalue()

    output = ""
    colour = discord.Colour.green()

    if sout and sout.strip():
      output += sout
    if serr and serr.strip():
      output += "\n" + serr
      colour = discord.Colour.red()

    if output:
      output = "\n".join([f'{i:03d} | {line}' for i, line in enumerate(output.split('\n'), 1)][:-1])
    else:
      output = "No output detected"

    embed = discord.Embed(
      title="Code Output",
      colour=colour
    ).add_field(
      name="Returned", value=f"```\n{result}```"
    ).add_field(
      name="Output", value=f"```py\n{output}```"
    )

    await ctx.reply(embed=embed)

  
  @commands.command(hidden=True)
  async def save_stats(self, ctx: commands.Context):
    result = await self.bot.shroom_farm.save_daily_stats(self.bot.shroom_farm.daily_stats)
    if result:
      msg = "Daily Stats was saved successfully"
    else:
      msg = "Daily Stats was unable to be saved"
    await ctx.reply(msg)

  
  @commands.command(hidden=True)
  async def show_server_stats(
    self,
    ctx: commands.Context,
    server_id: int | None = None
  ):
    if server_id is None:
      server_id = ctx.guild.id # type: ignore
    farm_stats = self.bot.shroom_farm.daily_stats.get_farm_stats(server_id)
    if farm_stats is not None:
      await ctx.reply(str(farm_stats))

  
  @commands.command(hidden=True)
  async def show_user_info(
    self,
    ctx: commands.Context,
    user_id: int | None = None
  ):
    if user_id is None:
      user_id = ctx.author.id
    user_info = await self.bot.shroom_farm.get_user(user_id)
    if user_info is not None:
      await ctx.reply(str(user_info))

  
  @commands.command(hidden=True)
  @commands.guild_only()
  async def force_setup(
    self,
    ctx: commands.Context,
    channel_id: int | None = None
  ):
    if channel_id is None:
      channel_id = ctx.channel.id
    try:
      await self.bot.shroom_farm.create_farm(ctx.guild.id, channel_id) # type: ignore
    except ValueError:
      embed = FARM_ALREADY_EXISTS
    else:
      embed = FARM_CREATE_SUCCESS(channel_id)
    await ctx.reply(embed=embed)

  
  @commands.command(hidden=True)
  @commands.guild_only()
  async def farm(
    self,
    ctx: commands.Context,
    amount: int,
    user_id: int | None = None
  ):
    if user_id is None:
      user_id = ctx.author.id

    farm = await self.bot.shroom_farm.get_farm(ctx.guild.id) # type: ignore

    if farm is None:
      return

    async with self.bot._lock:
      result = await self.bot.shroom_farm.farm(farm, ctx.author.id, amount) # type: ignore

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
          title=f"{ctx.author.name} ranked up!",
          description=f"Your rank is now `{result.user.next_rank.name}`!", # type: ignore
          colour=discord.Colour.green()
        )
      )
    
    await ctx.reply(embeds=embeds)