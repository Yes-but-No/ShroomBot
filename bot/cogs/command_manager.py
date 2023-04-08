from __future__ import annotations
import os
from traceback import print_exc

from typing import TYPE_CHECKING, Literal, Optional

from discord.ext import commands

if TYPE_CHECKING:
  from bot import ShroomBot


class CommandManager(commands.Cog):
  """Commands for managing cogs and application commands"""

  def __init__(self, bot: ShroomBot):
    self.bot = bot

  
  @commands.command()
  async def load_extension(self, ctx: commands.Context, ext: str):
    try:
      await self.bot.load_extension(ext)
    except Exception as e:
      print_exc()
      msg = f"Loading of extension `{ext}` failed with `{e}`"
    else:
      msg = f"Extension {ext} loaded successfully"
    await ctx.reply(msg, mention_author=False)

  @commands.command()
  async def unload_extension(self, ctx: commands.Context, ext: str):
    try:
      await self.bot.unload_extension(ext)
    except Exception as e:
      print_exc()
      msg = f"Unloading of extension `{ext}` failed with `{e}`"
    else:
      msg = f"Extension {ext} unloaded successfully"
    await ctx.reply(msg, mention_author=False)

  @commands.command()
  async def reload_extension(self, ctx: commands.Context, ext: str):
    try:
      await self.bot.reload_extension(ext)
    except Exception as e:
      print_exc()
      msg = f"Reloading of extension `{ext}` failed with `{e}`"
    else:
      msg = f"Extension {ext} reloaded successfully"
    await ctx.reply(msg, mention_author=False)


  @commands.command()
  async def sync(self, ctx: commands.Context, option: Optional[Literal["to_server", "clear_server"]] = None):
    if option == "to_server":
      self.bot.tree.copy_global_to(guild=self.bot.dev_server)
      synced = await self.bot.tree.sync(guild=self.bot.dev_server)
    elif option == "clear_server":
      self.bot.tree.clear_commands(guild=self.bot.dev_server)
      await self.bot.tree.sync(guild=self.bot.dev_server)
      synced = []
    else:
      synced = await self.bot.tree.sync()
    await ctx.reply(f"Synced {len(synced)} commands {'globally' if option is None else 'to development server'}")