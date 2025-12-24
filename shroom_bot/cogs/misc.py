from __future__ import annotations

from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from bot import ShroomBot


class Misc(commands.Cog):
    """Miscellaneous commands"""

    def __init__(self, bot: ShroomBot):
        self.bot = bot

    @app_commands.command(name="mini")
    async def mini(self, interaction: discord.Interaction):
        """What does this even do??"""
        await interaction.response.send_message("This command was developed by mini")

    @app_commands.command(name="jerome")
    async def jerome(self, interaction: discord.Interaction):
        """Get a random quote that Jerome definitely made"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://thequoteshub.com/api/random-quote?format=json"
            ) as r:
                if r.status == 200:
                    quote = (await r.json())["text"]  # type: ignore
                    embed = discord.Embed(
                        title="Jerome's Quote:",
                        description=quote,
                        colour=discord.Colour.random(),
                    )
                    embed.set_author(
                        name="Jerome",
                        icon_url=self.bot.user.display_avatar.url,  # type: ignore
                    )
                else:
                    embed = discord.Embed(
                        title="Error",
                        description="An internal error has occurred, please try again later",
                        colour=discord.Colour.red(),
                    )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="whyjerome")
    async def whyjerome(self, interaction: discord.Interaction):
        """Everyone asks who is Jerome, but never asks why Jerome"""
        embed = discord.Embed(
            title="Why Jerome:",
            description="The /jerome command gives a random quote",
            colour=discord.Colour.random(),
        )
        embed.set_author(name="Jerome", icon_url=self.bot.user.display_avatar.url)  # type: ignore
        embed.set_footer(text="/mini ♥ /jerome ")
        await interaction.response.send_message(embed=embed)


async def setup(bot: ShroomBot):
    await bot.add_cog(Misc(bot))
