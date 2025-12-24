from __future__ import annotations

from traceback import print_exc
from typing import TYPE_CHECKING, Literal

from discord.ext import commands

if TYPE_CHECKING:
    from shroom_bot.bot import ShroomBot


class CommandManager(commands.Cog):
    """Commands for managing cogs and application commands"""

    def __init__(self, bot: ShroomBot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
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
    @commands.is_owner()
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
    @commands.is_owner()
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
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        option: Literal["to_dev", "clear_dev"] | None = None,
    ):
        if option == "to_dev":
            self.bot.tree.copy_global_to(guild=self.bot.dev_server)
            synced = await self.bot.tree.sync(guild=self.bot.dev_server)
        elif option == "clear_dev":
            self.bot.tree.clear_commands(guild=self.bot.dev_server)
            await self.bot.tree.sync(guild=self.bot.dev_server)
            synced = []
        else:
            synced = await self.bot.tree.sync()

        await ctx.reply(
            f"Synced {len(synced)} commands {'globally' if option is None else 'to development server'}.",
            mention_author=False,
        )


async def setup(bot: ShroomBot) -> None:
    await bot.add_cog(CommandManager(bot))
