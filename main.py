from __future__ import annotations

import datetime
import os

import discord
from discord import app_commands

from bot import ShroomBot


bot = ShroomBot(command_prefix="$", help_command=None, intents=discord.Intents.all())

@bot.tree.command(name="setup")
@app_commands.describe(channel="The channel where you want mushrooms to be farmed")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def setup_farm(interaction: discord.Interaction, channel: discord.TextChannel):
  """Setup the farm in your server to start farming!"""
  try:
    await bot.shroom_farm.create_farm(interaction.guild_id, channel.id) # type: ignore
  except ValueError:
    embed =  discord.Embed(
      title="Farm already exists!",
      description="Your server already has a farm set up, if you wish to change the farm channel, use `/setchannel` instead",
      colour=discord.Colour.red()
    )
  else:
    embed = discord.Embed(
      title="Success!",
      description=f"Farm created successfully, send a 🍄 in <#{channel.id}> to start farming!",
      colour=discord.Colour.green()
    )
  await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setchannel")
@app_commands.describe(channel="The channel where you want mushrooms to be farmed")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
  """Change the the farm channel for your server"""
  try:
    await bot.shroom_farm.set_farm_channel(interaction.guild_id, channel.id) # type: ignore
  except ValueError:
    embed = discord.Embed(
      title="Farm not set up!",
      description="Your server has not set up the farm yet, use `/setup` instead",
      colour=discord.Colour.red()
    )
  else:
    embed = discord.Embed(
      title="Success!",
      description=f"The farm channel has been successfully changed to <#{channel.id}>",
      colour=discord.Colour.green()
    )
  await interaction.response.send_message(embed=embed)

@bot.tree.command(name="farmstats")
@app_commands.guild_only()
async def farm_stats(interaction: discord.Interaction):
  """Get the farm stats of your server"""
  farm = await bot.shroom_farm.get_farm(interaction.guild_id) # type: ignore
  if farm is None or farm.farm_channel is None:
    embed = discord.Embed(
      title="Farm not set up!",
      description="Use `/setup` to setup your server and start farming!",
      colour=discord.Colour.red()
    )
  else:
    farmed_today = bot.shroom_farm.get_server_farmed_today(interaction.guild_id) # type: ignore
    farmed_weekly = await bot.shroom_farm.get_server_weekly_farmed(interaction.guild_id) # type: ignore
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
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url) # type: ignore
    embed.set_footer(text=f'Requested by {interaction.user!s}', icon_url=interaction.user.display_avatar.url)
  await interaction.response.send_message(embed=embed)

@bot.tree.context_menu(name="User Stats")
async def user_stats(interaction: discord.Interaction, member: discord.Member):
  user = await bot.shroom_farm.get_user(member.id) # type: ignore
  if user is None:
    embed = discord.Embed(
      title="Account not found!",
      description="User has not started farming yet",
      colour=discord.Colour.red()
    )
  else:
    farmed_today = bot.shroom_farm.get_user_farmed_today(member.id) # type: ignore
    farmed_weekly = await bot.shroom_farm.get_user_weekly_farmed(member.id) # type: ignore
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
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url) # type: ignore
    embed.set_footer(text="Started farming")
  await interaction.response.send_message(embed=embed)

bot.run(os.getenv("TOKEN")) # type: ignore