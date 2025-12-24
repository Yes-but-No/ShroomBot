from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from shroom_bot import embeds
from shroom_bot.checks import under_maintenance

if TYPE_CHECKING:
    from shroom_bot.bot import ShroomBot


@app_commands.guild_only()
class Farm(commands.GroupCog, group_name="farm"):
    def __init__(self, bot: ShroomBot):
        self.bot = bot

    @app_commands.command(name="setup")
    @app_commands.describe(channel="The channel where you want mushrooms to be farmed")
    @under_maintenance()
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_farm(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Setup the farm in your server to start farming!"""
        try:
            await self.bot.game.create_farm(interaction.guild_id, channel.id)  # type: ignore
        except ValueError:
            embed = embeds.farm_already_exists()
        else:
            embed = embeds.farm_create_success(channel.id)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchannel")
    @app_commands.describe(channel="The channel where you want mushrooms to be farmed")
    @under_maintenance()
    @app_commands.checks.has_permissions(administrator=True)
    async def set_farm_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Change the farm channel to a different channel."""
        try:
            await self.bot.game.set_farm_channel(interaction.guild_id, channel.id)  # type: ignore
        except ValueError:
            embed = embeds.change_farm_channel_not_set_up()
        else:
            embed = embeds.channel_change_success(channel.id)
        await interaction.response.send_message(embed=embed)


async def setup(bot: ShroomBot):
    await bot.add_cog(Farm(bot))
