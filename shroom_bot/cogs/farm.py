from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from shroom_bot import embeds
from shroom_bot.checks import under_maintenance
from shroom_bot.game.ranks import get_rank_info

if TYPE_CHECKING:
    from shroom_bot.bot import ShroomBot


@app_commands.guild_only()
class Farm(commands.GroupCog, group_name="farm"):
    def __init__(self, bot: ShroomBot):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="User Stats", callback=self.user_stats_ctx_menu
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    @app_commands.command(name="setup")
    @app_commands.describe(channel="The channel where you want mushrooms to be farmed")
    @under_maintenance()
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_farm(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Setup the farm in your server to start farming!"""
        async with self.bot.game.autosave():
            result = await self.bot.game.create_server(interaction.guild_id, channel.id)  # type: ignore
        if result:
            embed = embeds.farm_create_success(channel.id)
        else:
            embed = embeds.farm_already_exists()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchannel")
    @app_commands.describe(channel="The channel where you want mushrooms to be farmed")
    @under_maintenance()
    @app_commands.checks.has_permissions(administrator=True)
    async def set_farm_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        """Change the farm channel to a different channel."""
        async with self.bot.game.autosave():
            result = await self.bot.game.set_farm_channel(
                interaction.guild_id,  # type: ignore
                channel.id,
            )
        if result:
            embed = embeds.channel_change_success(channel.id)
        else:
            embed = embeds.change_farm_channel_not_set_up()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setdailygoal")
    @app_commands.describe(goal="The target number of mushrooms to farm each day")
    @under_maintenance()
    @app_commands.checks.has_permissions(administrator=True)
    async def set_goal(self, interaction: discord.Interaction, goal: int):
        """Set the daily goal for server members to work towards"""
        async with self.bot.game.autosave():
            result = await self.bot.game.set_server_daily_goal(
                interaction.guild_id,  # type: ignore
                goal,
            )
        if result:
            _embed = embeds.set_daily_goal_success(goal)
        else:
            _embed = embeds.farm_not_set_up()
        await interaction.response.send_message(embed=_embed)

    @app_commands.command(name="serverstats")
    async def server_stats(self, interaction: discord.Interaction):
        """Get the farm stats of your server"""
        server = await self.bot.game.get_server(interaction.guild_id)  # type: ignore
        if server is None:
            _embed = embeds.farm_not_set_up()
        else:
            _stats_date = self.bot.get_stats_date()

            _stats_today = await self.bot.game.get_daily_server_stats(
                server.server_id,
                _stats_date,
            )
            farmed_today = _stats_today.daily_count if _stats_today is not None else 0

            _week_start = _stats_date - timedelta(days=_stats_date.weekday())
            _week_end = _week_start + timedelta(days=6)
            farmed_this_week = await self.bot.game.get_server_timespan_farmed(
                server.server_id, _week_start, _week_end
            )

            farmed_ever = server.lifetime_farmed

            _embed = (
                embeds.farm_stats(
                    interaction.guild.name,  # type: ignore
                    farmed_today,
                    farmed_this_week,
                    farmed_ever,
                    server.daily_goal if server.daily_goal > 0 else None,
                    server.farm_channel_id,
                    server.last_farmer_id,
                    server.best_daily,
                    server.best_weekly,
                )
                .set_author(
                    name=self.bot.user.name,  # type: ignore
                    icon_url=self.bot.user.display_avatar.url,  # type: ignore
                )
                .set_footer(
                    text=f"Requested by {interaction.user!s}",
                    icon_url=interaction.user.display_avatar.url,
                )
            )

        await interaction.response.send_message(embed=_embed)

    @app_commands.command(name="userstats")
    async def user_stats(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ):
        """Get the stats of a user"""
        if member is None:
            assert isinstance(interaction.user, discord.Member)
            member = interaction.user

        user = await self.bot.game.get_user(member.id)
        if user is None:
            _embed = embeds.account_not_found()
        else:
            _stats_date = self.bot.get_stats_date()
            _stats_today = await self.bot.game.get_daily_user_stats(
                interaction.guild_id,  # type: ignore
                member.id,
                _stats_date,
            )
            farmed_today = _stats_today.farmed if _stats_today is not None else 0

            _week_start = _stats_date - timedelta(days=_stats_date.weekday())
            _week_end = _week_start + timedelta(days=6)
            farmed_this_week = await self.bot.game.get_user_timespan_farmed(
                interaction.guild_id,  # type: ignore
                member.id,
                _week_start,
                _week_end,
            )

            rank_info = get_rank_info(user.lifetime_farmed)

            _embed = embeds.user_stats(
                member.display_name,
                user.created_at,  # type: ignore
                rank_info,
                user.tokens,
                farmed_today,
                farmed_this_week,
                user.lifetime_farmed,
            ).set_author(
                name=self.bot.user.name,  # type: ignore
                icon_url=self.bot.user.display_avatar.url,  # type: ignore
            )

        await interaction.response.send_message(embed=_embed)

    async def user_stats_ctx_menu(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        user = await self.bot.game.get_user(member.id)
        if user is None:
            _embed = embeds.account_not_found()
        else:
            _stats_date = self.bot.get_stats_date()
            _stats_today = await self.bot.game.get_daily_user_stats(
                interaction.guild_id,  # type: ignore
                member.id,
                _stats_date,
            )
            farmed_today = _stats_today.farmed if _stats_today is not None else 0

            _week_start = _stats_date - timedelta(days=_stats_date.weekday())
            _week_end = _week_start + timedelta(days=6)
            farmed_this_week = await self.bot.game.get_user_timespan_farmed(
                interaction.guild_id,  # type: ignore
                member.id,
                _week_start,
                _week_end,
            )

            rank_info = get_rank_info(user.lifetime_farmed)

            _embed = embeds.user_stats(
                member.display_name,
                user.created_at,  # type: ignore
                rank_info,
                user.tokens,
                farmed_today,
                farmed_this_week,
                user.lifetime_farmed,
            ).set_author(
                name=self.bot.user.name,  # type: ignore
                icon_url=self.bot.user.display_avatar.url,  # type: ignore
            )

        await interaction.response.send_message(embed=_embed)


async def setup(bot: ShroomBot):
    await bot.add_cog(Farm(bot))
