from __future__ import annotations

import contextlib
import datetime
import re
import traceback
from io import StringIO
from typing import TYPE_CHECKING

import discord
from attrs import asdict
from discord.ext import commands

from shroom_bot import embeds

if TYPE_CHECKING:
    from shroom_bot.bot import ShroomBot


class Debug(commands.Cog):
    def __init__(self, bot: ShroomBot):
        self.bot = bot

    @commands.command(aliases=["eval"])
    @commands.is_owner()
    async def exec(self, ctx: commands.Context, *, code: str):
        line_break = "\n"

        code_block = re.findall(r"```([a-zA-Z0-9]*)\s([\s\S(^\\`{3})]*?)\s*```", code)
        code = code_block[0][1]

        sout = StringIO()
        serr = StringIO()

        exec_vars = {"discord": discord}

        with contextlib.redirect_stdout(sout), contextlib.redirect_stderr(serr):
            try:
                func = (
                    "async def exec_func(ctx, bot):\n"
                    f"{line_break.join((' ' * 2 + line) for line in code.split(line_break))}"
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
            if output:
                output += "\n"
            output += serr
            colour = discord.Colour.red()

        if output == "":
            output = "No output"

        _embed = (
            discord.Embed(title="Code Output", colour=colour)
            .add_field(name="Returned", value=f"```\n{result}```", inline=False)
            .add_field(name="Output", value=f"```py\n{output}```", inline=False)
        )

        await ctx.reply(embed=_embed)

    @commands.command()
    async def reinvoke(
        self, ctx: commands.Context, message: discord.Message | None = None
    ):
        if message is None:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)  # type: ignore
        await self.bot.process_commands(message)

    @commands.command()
    @commands.guild_only()
    async def force_setup(self, ctx: commands.Context, channel_id: int | None = None):
        if channel_id is None:
            channel_id = ctx.channel.id
        async with self.bot.game.autosave():
            result = await self.bot.game.create_server(ctx.guild.id, channel_id)  # type: ignore
        if result:
            _embed = embeds.farm_create_success(channel_id)
        else:
            _embed = embeds.farm_already_exists()
        await ctx.reply(embed=_embed)

    @commands.command()
    @commands.guild_only()
    async def farm(
        self, ctx: commands.Context, amount: int, user_id: int | None = None
    ):
        if user_id is None:
            user_id = ctx.author.id

        farm = await self.bot.game.get_server(ctx.guild.id)  # type: ignore

        if farm is None:
            return

        await self.bot.farm(
            farm.server_id,
            ctx.message,
            user_id=user_id,
            amount=amount,
            ignore_last=True,
        )

    @commands.command()
    async def toggle_maintenance(self, ctx: commands.Context):
        mode = self.bot.maintenance_mode = not self.bot.maintenance_mode

        await ctx.reply(f"Maintenance mode {'enabled' if mode else 'disabled'}")

    @commands.command()
    async def show_server_stats(
        self,
        ctx: commands.Context,
        server: discord.Guild | None = None,
        stat_date: str | None = None,
    ):
        if server is None:
            if ctx.guild is None:
                await ctx.reply("Please specify a server")
                return
            server = ctx.guild

        if stat_date is None:
            stats_date = self.bot.get_stats_date()
        else:
            stats_date = datetime.datetime.strptime(stat_date, "%Y-%m-%d").date()

        server_stats = await self.bot.game.get_daily_server_stats(server.id, stats_date)
        if server_stats is not None:
            await ctx.reply(f"```py\n{asdict(server_stats)}```")
        else:
            await ctx.reply("Server's stats not found")

    @commands.command()
    async def show_user_stats(
        self,
        ctx: commands.Context,
        server: discord.Guild | None = None,
        user: discord.User | None = None,
        stat_date: str | None = None,
    ):
        if server is None:
            if ctx.guild is None:
                await ctx.reply("Please specify a server")
                return
            server = ctx.guild

        if user is None:
            user_id = ctx.author.id
        else:
            user_id = user.id

        if stat_date is None:
            stats_date = self.bot.get_stats_date()
        else:
            stats_date = datetime.datetime.strptime(stat_date, "%Y-%m-%d").date()

        user_stats = await self.bot.game.get_daily_user_stats(
            server.id, user_id, stats_date
        )
        if user_stats is not None:
            await ctx.reply(f"```py\n{asdict(user_stats)}```")
        else:
            await ctx.reply("User's stats not found")

    @commands.command()
    async def show_server_info(
        self, ctx: commands.Context, server: discord.Guild | None = None
    ):
        if server is None:
            if ctx.guild is None:
                await ctx.reply("Please specify a server")
                return
            server = ctx.guild

        server_info = await self.bot.game.get_server(server.id)
        if server_info is not None:
            await ctx.reply(f"```py\n{asdict(server_info)}```")
        else:
            await ctx.reply("Server not found")

    @commands.command()
    async def show_user_info(
        self, ctx: commands.Context, user: discord.User | None = None
    ):
        if user is None:
            user_id = ctx.author.id
        else:
            user_id = user.id

        user_info = await self.bot.game.get_user(user_id)
        if user_info is not None:
            await ctx.reply(f"```py\n{asdict(user_info)}```")
        else:
            await ctx.reply("User not found")


async def setup(bot: ShroomBot):
    await bot.add_cog(Debug(bot))
