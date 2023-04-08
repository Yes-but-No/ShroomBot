from __future__ import annotations
import datetime

from discord import app_commands
from discord.ext import commands
import discord

from typing import TYPE_CHECKING, Optional

from bot.embeds import (
  ACCOUNT_NOT_FOUND,
  CHANGE_FARM_CHANNEL_NOT_SET_UP,
  CHANNEL_CHANGE_SUCCESS,
  FARM_ALREADY_EXISTS,
  FARM_CREATE_SUCCESS,
  FARM_NOT_SET_UP,
  SET_DAILY_GOAL_SUCCESS
)

if TYPE_CHECKING:
  from bot import ShroomBot


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
  @app_commands.checks.has_permissions(administrator=True)
  async def setup_farm(
    self,
    interaction: discord.Interaction,
    channel: discord.TextChannel
  ):
    """Setup the farm in your server to start farming!"""
    try:
      await self.bot.shroom_farm.create_farm(interaction.guild_id, channel.id) # type: ignore
    except ValueError:
      embed = FARM_ALREADY_EXISTS
    else:
      embed = FARM_CREATE_SUCCESS(channel.id)
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name="setchannel")
  @app_commands.describe(channel="The channel where you want mushrooms to be farmed")
  @app_commands.checks.has_permissions(administrator=True)
  async def set_channel(
    self,
    interaction: discord.Interaction,
    channel: discord.TextChannel
  ):
    """Change the the farm channel for your server"""
    try:
      await self.bot.shroom_farm.set_farm_channel(interaction.guild_id, channel.id) # type: ignore
    except ValueError:
      embed = CHANGE_FARM_CHANNEL_NOT_SET_UP
    else:
      embed = CHANNEL_CHANGE_SUCCESS(channel.id)
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name="setdailygoal")
  @app_commands.describe(goal="The target number of mushrooms to farm each day")
  @app_commands.checks.has_permissions(administrator=True)
  async def set_goal(
    self,
    interaction: discord.Interaction,
    goal: int
  ):
    """Set the daily goal for server members to work towards"""
    try:
      await self.bot.shroom_farm.set_daily_goal(interaction.guild_id, goal) # type: ignore
    except ValueError:
      embed = FARM_NOT_SET_UP
    else:
      embed = SET_DAILY_GOAL_SUCCESS(goal)
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name="farmstats")
  async def farm_stats(
    self,
    interaction: discord.Interaction
  ):
    """Get the farm stats of your server"""
    farm = await self.bot.shroom_farm.get_farm(interaction.guild_id) # type: ignore
    if farm is None or farm.farm_channel is None:
      embed = FARM_NOT_SET_UP
    else:
      farmed_today = self.bot.shroom_farm.get_server_farmed_today(interaction.guild_id) # type: ignore
      farmed_weekly = await self.bot.shroom_farm.get_server_weekly_farmed(interaction.guild_id) # type: ignore
      farmed_ever = farm.total_farmed
      embed = discord.Embed(
        title=f"Farm Stats for {interaction.guild.name}", # type: ignore
        timestamp=datetime.datetime.now(),
        colour=discord.Colour.random()
      ).add_field(
        name="Farmed Today", value=farmed_today
      ).add_field(
        name="Farmed This Week", value=farmed_weekly
      ).add_field(
        name="Farmed Ever", value=farmed_ever
      ).add_field(
        name="Daily Goal", value=farm.daily_goal
      ).add_field(
        name="Farming Channel", value=f"<#{farm.farm_channel}>", inline=False
      )
      embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url) # type: ignore
      embed.set_footer(text=f'Requested by {interaction.user!s}', icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)


  @app_commands.command(name="userstats")
  async def user_stats(
    self,
    interaction: discord.Interaction,
    member: Optional[discord.Member] = None
  ):
    """Get the stats of a user"""
    if member is None:
      member = interaction.user # type: ignore
    else:
      member = member
    user = await self.bot.shroom_farm.get_user(member.id) # type: ignore
    if user is None:
      embed = ACCOUNT_NOT_FOUND
    else:
      farmed_today = self.bot.shroom_farm.get_user_farmed_today(member.id) # type: ignore
      farmed_weekly = await self.bot.shroom_farm.get_user_weekly_farmed(member.id) # type: ignore
      farmed_ever = user.farmed
      embed = discord.Embed(
        title=f"{member.name}'s Stats", # type: ignore
        timestamp=user.joined.replace(tzinfo=datetime.timezone.utc),
        colour=discord.Colour.random()
      ).add_field(
        name="Rank", value=user.rank.name
      ).add_field(
        name="Next Rank Requirement",
        value=f"{user.next_rank.requirement} Shrooms"
              if user.next_rank is not None else "None"
      ).add_field(
        name="Shroom Tokens", value=user.tokens
      ).add_field(
        name="Farmed Today", value=farmed_today
      ).add_field(
        name="Farmed This Week", value=farmed_weekly
      ).add_field(
        name="Farmed Ever", value=farmed_ever
      )
      embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url) # type: ignore
      embed.set_footer(text="Started farming")
    await interaction.response.send_message(embed=embed)


  async def user_stats_ctx_menu(
    self,
    interaction: discord.Interaction,
    member: discord.Member
  ):
    user = await self.bot.shroom_farm.get_user(member.id)
    if user is None:
      embed = ACCOUNT_NOT_FOUND
    else:
      farmed_today = self.bot.shroom_farm.get_user_farmed_today(member.id)
      farmed_weekly = await self.bot.shroom_farm.get_user_weekly_farmed(member.id)
      farmed_ever = user.farmed
      embed = discord.Embed(
        title=f"{member.name}'s Stats",
        timestamp=user.joined.replace(tzinfo=datetime.timezone.utc),
        colour=discord.Colour.random()
      ).add_field(
        name="Rank", value=user.rank.name
      ).add_field(
        name="Next Rank Requirement",
        value=f"{user.next_rank.requirement} Shrooms"
              if user.next_rank is not None else "None"
      ).add_field(
        name="Shroom Tokens", value=user.tokens
      ).add_field(
        name="Farmed Today", value=farmed_today
      ).add_field(
        name="Farmed This Week", value=farmed_weekly
      ).add_field(
        name="Farmed Ever", value=farmed_ever
      )
      embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.display_avatar.url) # type: ignore
      embed.set_footer(text="Started farming")
    await interaction.response.send_message(embed=embed)


async def setup(bot: ShroomBot):
  await bot.add_cog(Farm(bot))