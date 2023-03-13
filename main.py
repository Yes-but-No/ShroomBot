from __future__ import annotations
import asyncio

import datetime
import os
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from shroom import ShroomFarm

if TYPE_CHECKING:
  from discord import Message
  from shroom import Farm

DEV_SERVER = discord.Object(id=os.getenv("DEV_SERVER_ID"))
SHROOM_RESET_TIME = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)
DATABASE_URL = os.getenv("MONGO_URL")

def int_to_ordinal(n: int) -> str:
  s = str(n)
  if s[-1] == "1":
    s += "st"
  elif s[-1] == "2":
    s += "nd"
  elif s[-1] == "3":
    s += "rd"
  else:
    s += "th"
  return s

def get_farm_stats_embed(farm: Farm, server: discord.Guild) -> discord.Embed:
  return discord.Embed(
    title=f"Farm Stats for {server.name}",
    timestamp=datetime.datetime.now(),
    colour=discord.Colour.random()
  ).add_field(
    name="Farmed Today", value=farm.farmed_today
  ).add_field(
    name="Farmed Ever", value=farm.total_farmed
  ).add_field(
    name="Farming Channel", value=f"<#{farm.farm_channel}>", inline=False
  )



class ShroomBot(commands.Bot):
  def __init__(self, *args, **kwargs):
    self.shroom_farm = ShroomFarm(DATABASE_URL)
    self.owner_ids = (751768586699276342, 759195783597129760)
    self._lock = asyncio.Lock()
    super().__init__(*args, **kwargs)

  @tasks.loop(time=datetime.time(0, 0, tzinfo=datetime.timezone.utc))
  async def reset_count_loop(self):
    async with self._lock:
      await self.shroom_farm.reset_daily_count()

  async def setup_hook(self) -> None:
    await self.shroom_farm.load_farms()
    await self.shroom_farm.reset_daily_count()

    self.tree.copy_global_to(guild=DEV_SERVER)
    await self.tree.sync(guild=DEV_SERVER)

  async def on_message(self, message: Message):
    if message.author.bot:
      return

    if message.content == "🍄":
      farm = self.shroom_farm.get_farm(message.guild.id)
      if farm is None or farm.farm_channel is None:
        embed = discord.Embed(
          title="Farm not set up!",
          description="Use `/setup` to setup your server and start farming!",
          colour=discord.Colour.red()
        )
      elif farm.farm_channel != message.channel.id:
        return
      elif farm.last_farmer == message.author.id:
        embed = discord.Embed(
          title="You cannot farm mushrooms now",
          description="You can only farm mushrooms one at a time",
          colour=discord.Colour.red()
        )
      else:
        farmed = await self.shroom_farm.farm(message.guild.id, message.author.id)
        await message.add_reaction("🍄")
        embed = discord.Embed(
          title="Mushroom farmed!",
          description=f"{int_to_ordinal(farmed)} mushroom farmed today!",
          colour=discord.Colour.green()
        )
      await message.reply(embed=embed)
    else:
      await self.process_commands(message)



bot = ShroomBot(command_prefix="$", help_command=None, intents=discord.Intents.all())

@bot.command(hidden=True)
@commands.is_owner()
async def edit_count(ctx: commands.Context, amount: int, server_id: int | None = None):
  if server_id is None:
    server_id = ctx.guild.id
  farm = bot.shroom_farm.get_farm(server_id)
  if farm is not None:
    farm.farmed_today = amount
    await bot.shroom_farm.save_farm(farm)
    await ctx.reply(f"Shroom count changed to {amount}")
  else:
    await ctx.reply("No server specified")

@bot.tree.command(name="setup")
@app_commands.describe(channel="The channel where you want mushrooms to be farmed")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def setup_farm(interaction: discord.Interaction, channel: discord.TextChannel):
  """Setup the farm in your server to start farming!"""
  try:
    await bot.shroom_farm.create_farm(interaction.guild_id, channel.id)
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
    await bot.shroom_farm.set_farm_channel(interaction.guild_id, channel.id)
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
  farm = bot.shroom_farm.get_farm(interaction.guild_id)
  if farm is None or farm.farm_channel is None:
    embed = discord.Embed(
      title="Farm not set up!",
      description="Use `/setup` to setup your server and start farming!",
      colour=discord.Colour.red()
    )
  else:
    embed = get_farm_stats_embed(farm, interaction.guild)
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.set_footer(text=f'Requested by {interaction.user!s}', icon_url=interaction.user.display_avatar.url)
  await interaction.response.send_message(embed=embed)

@bot.tree.context_menu(name="User Stats")
async def user_stats(interaction: discord.Interaction, member: discord.Member):
  user = await bot.shroom_farm.get_user(member.id)
  if user is None:
    embed = discord.Embed(
      title="Account not found!",
      description="User has not started farming yet",
      colour=discord.Colour.red()
    )
  else:
    embed = discord.Embed(
      title=f"{member.name}'s Stats",
      description=f"{member.name} has farmed a total of {user['farmed']} mushrooms!",
      colour=discord.Colour.random(),
      timestamp=user["joined"].replace(tzinfo=datetime.timezone.utc)
    )
    embed.set_author(name=bot.user.name, icon_url=bot.user.display_avatar.url)
    embed.set_footer(text="Started farming")
  await interaction.response.send_message(embed=embed)


bot.run(os.getenv("TOKEN"))