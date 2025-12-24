from __future__ import annotations

import contextlib
import re
import traceback
from io import StringIO
from typing import TYPE_CHECKING

import discord
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
        try:
            await self.bot.game.create_farm(ctx.guild.id, channel_id)  # type: ignore
        except ValueError:
            _embed = embeds.farm_already_exists()
        else:
            _embed = embeds.farm_create_success(channel_id)
        await ctx.reply(embed=_embed)

    @commands.command()
    @commands.guild_only()
    async def farm(
        self, ctx: commands.Context, amount: int, user_id: int | None = None
    ):
        if user_id is None:
            user_id = ctx.author.id

        farm = await self.bot.game.get_farm(ctx.guild.id)  # type: ignore

        if farm is None:
            return

        await self.bot.farm(
            farm, ctx.message, user_id=user_id, amount=amount, ignore_last=True
        )

    @commands.command()
    async def toggle_maintenance(self, ctx: commands.Context):
        mode = self.bot.maintenance_mode = not self.bot.maintenance_mode

        await ctx.reply(f"Maintenance mode {'enabled' if mode else 'disabled'}")


async def setup(bot: ShroomBot):
    await bot.add_cog(Debug(bot))
