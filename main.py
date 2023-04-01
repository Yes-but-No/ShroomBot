from __future__ import annotations

import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands

from bot import ShroomBot
from utils import int_to_ordinal

DATABASE_URL = os.getenv("MONGO_URL")

if DATABASE_URL is None:
  url = "localhost"
else:
  url = DATABASE_URL

print("Connecting to database at:", url)

bot = ShroomBot(mongo_url=url, command_prefix="$", help_command=None, intents=discord.Intents.all(), owner_ids=(751768586699276342, 759195783597129760))


#########################
### Text Debug Commands
#########################

@bot.command(hidden=True)
@commands.is_owner()
async def save_stats(ctx: commands.Context):
  await bot.shroom_farm.save_daily_stats(bot.shroom_farm.daily_stats)

@bot.command(hidden=True)
@commands.is_owner()
async def show_server_stats(ctx: commands.Context, server_id: int):
  farm_stats = bot.shroom_farm.daily_stats.get_farm_stats(server_id) # type: ignore
  if farm_stats is not None:
    await ctx.reply(str(farm_stats))

@bot.command(hidden=True)
@commands.is_owner()
async def show_user_info(ctx: commands.Context, user_id: int | None = None):
  if user_id is None:
    user_id = ctx.author.id
  user_info = await bot.shroom_farm.get_user(user_id) # type: ignore
  if user_info is not None:
    await ctx.reply(str(user_info))

@bot.command(hidden=True)
@commands.is_owner()
@commands.guild_only()
async def force_setup(ctx: commands.Context, channel_id: int | None = None):
  if channel_id is None:
    channel_id = ctx.channel.id
  try:
    await bot.shroom_farm.create_farm(ctx.guild.id, channel_id) # type: ignore
  except ValueError:
    embed =  discord.Embed(
      title="Farm already exists!",
      description="Your server already has a farm set up, if you wish to change the farm channel, use `/setchannel` instead",
      colour=discord.Colour.red()
    )
  else:
    embed = discord.Embed(
      title="Success!",
      description=f"Farm created successfully, send a 🍄 in <#{channel_id}> to start farming!",
      colour=discord.Colour.green()
    )
  await ctx.reply(embed=embed)

@bot.command(hidden=True)
@commands.is_owner()
@commands.guild_only()
async def force_set_channel(ctx: commands.Context, channel_id: int | None = None):
  if channel_id is None:
    channel_id = ctx.channel.id
  try:
    await bot.shroom_farm.set_farm_channel(ctx.guild.id, channel_id) # type: ignore
  except ValueError:
    embed = discord.Embed(
      title="Farm not set up!",
      description="Your server has not set up the farm yet, use `/setup` instead",
      colour=discord.Colour.red()
    )
  else:
    embed = discord.Embed(
      title="Success!",
      description=f"The farm channel has been successfully changed to <#{channel_id}>",
      colour=discord.Colour.green()
    )
  await ctx.reply(embed=embed)

@bot.command(hidden=True)
@commands.is_owner()
@commands.guild_only()
async def farm(ctx: commands.Context, amount: int, user_id: int | None = None):
  if user_id is None:
    user_id = ctx.author.id

  farm = await bot.shroom_farm.get_farm(ctx.guild.id) # type: ignore

  if farm is None:
    return

  result = await bot.shroom_farm.farm(farm, user_id, amount) # type: ignore

  farm_stats = result["farm_stats"]

  embeds = []

  embed = discord.Embed(
    title="Mushroom farmed!",
    description=f"{int_to_ordinal(farm_stats.farmed)} mushroom farmed today!",
    colour=discord.Colour.green()
  )
  # If we have not reached daily goal, show how many more to the daily goal
  if (
    not farm_stats.daily_goal_reached
    and farm_stats.daily_goal is not None
  ):
    embed.description += f"\n{farm_stats.daily_goal-farm_stats.farmed} more mushrooms till the daily goal!" # type: ignore
  
  embeds.append(embed)

  # Check if server has reached daily goal
  if all((
    farm_stats.daily_goal is not None,
    farm_stats.daily_goal_reached,
    not farm_stats.awarded_daily
  )):
    await bot.shroom_farm.award_contributors(farm_stats)
    embeds.append(
      discord.Embed(
        title="Daily goal reached!",
        description="All contributors have been awarded double Shroom Tokens!",
        colour=discord.Colour.green()
      )
    )

  # Check if user has ranked up
  user = result["user"]
  if user.ranked_up:
    await bot.shroom_farm.rank_up_user(user._id)
    embeds.append(
      discord.Embed(
        title=f"{ctx.author.name} ranked up!",
        description=f"Your rank is now `{user.next_rank.name}`!", # type: ignore
        colour=discord.Colour.green()
      )
    )
  
  await ctx.reply(embeds=embeds)

###############################
### Game Application Commands
###############################

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

@bot.tree.command(name="setdailygoal")
@app_commands.describe(goal="The target number of mushrooms to farm each day")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def set_goal(interaction: discord.Interaction, goal: int):
  """Set the daily goal for server members to work towards"""
  try:
    await bot.shroom_farm.set_daily_goal(interaction.guild_id, goal) # type: ignore
  except ValueError:
    embed = discord.Embed(
      title="Farm not set up!",
      description="Your server has not set up the farm yet, use `/setup` instead",
      colour=discord.Colour.red()
    )
  else:
    embed = discord.Embed(
      title="Success!",
      description=(
        f"The daily goal has been successfully changed to `{goal}`\n"
        "If you have already farmed mushrooms today, the daily goal will only apply tomorrow!"
      ),
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

###############################
### Misc Application Commands
###############################

@bot.tree.command(name="mini")
async def mini(interaction: discord.Interaction):
  """What does this even do??"""
  await interaction.response.send_message("This command was developed by mini")

####################
### Error handling
####################

default_on_error = bot.tree.on_error

@bot.tree.error
async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
  if isinstance(error, app_commands.MissingPermissions):
    msg = "You do not have the required permissions to run this command"
  else:
    msg = "An unknown error has occurred"
    await default_on_error(interaction, error) # type: ignore
  await interaction.response.send_message(
    embed=discord.Embed(
      title="Error!",
      description=msg,
      colour=discord.Colour.red()
    )
  )

bot.run(os.getenv("TOKEN")) # type: ignore