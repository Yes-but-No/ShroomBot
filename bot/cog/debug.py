from __future__ import annotations

import contextlib
import re
from io import StringIO
import traceback
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.embeds import FARM_ALREADY_EXISTS, FARM_CREATE_SUCCESS

if TYPE_CHECKING:
  from bot import ShroomBot

class Debug(commands.Cog):
  def __init__(self, bot: ShroomBot):
    self.bot = bot
  
  @commands.command(aliases=["eval"])
  @commands.is_owner() # We leave this here just in case
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

    exec_vars = {
      "discord": discord
    }
  
    with (
      contextlib.redirect_stdout(sout),
      contextlib.redirect_stderr(serr)
    ):
      try:
        func = (
          "async def exec_func(ctx, bot):\n"
          f"{line_break.join((' '*2 + line) for line in code.split(line_break))}"
        )
        exec(func, exec_vars.update(locals()))

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
      name="Returned", value=f"```\n{result}```", inline=False
    ).add_field(
      name="Output", value=f"```py\n{output}```", inline=False
    )

    await ctx.reply(embed=embed)

  
  @commands.command()
  async def save_stats(self, ctx: commands.Context):
    result = await self.bot.shroom_farm.save_daily_stats(self.bot.shroom_farm.daily_stats)
    if result:
      msg = "Daily Stats was saved successfully"
    else:
      msg = "Daily Stats was unable to be saved"
    await ctx.reply(msg)

  
  @commands.command()
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

  
  @commands.command()
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

  
  @commands.command()
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

  
  @commands.command()
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
    
    await self.bot.farm(farm, ctx.message, user_id, amount)


async def setup(bot: ShroomBot):
  await bot.add_cog(Debug(bot))