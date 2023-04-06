from __future__ import annotations

import os
import aiohttp

import discord
from discord import app_commands

from bot import ShroomBot

import aiohttp

DATABASE_URL = os.getenv("MONGO_URL")

if DATABASE_URL is None:
  url = "localhost"
else:
  url = DATABASE_URL

print("Connecting to database at:", url)

bot = ShroomBot(mongo_url=url, command_prefix="$", help_command=None, intents=discord.Intents.all(), owner_ids=(751768586699276342, 759195783597129760))

###############################
### Misc Application Commands
###############################

@bot.tree.command(name="mini")
async def mini(interaction: discord.Interaction):
  """What does this even do??"""
  await interaction.response.send_message("This command was developed by mini")
  
@bot.tree.command(name="jerome")
async def jerome(interaction: discord.Interaction):
  async with aiohttp.ClientSession() as session:
    async with session.get("https://api.quotable.io/random") as r:
      if r.status == 200:
        quote = r.json()["content"] # type: ignore
        embed = discord.Embed(
          title="Jerome's Quote:",
          description=quote,
          colour=discord.Colour.random()
        )
        embed.set_author(name='Jerome', icon_url=bot.user.display_avatar.url) # type: ignore
      else:
        embed = discord.Embed(
          title="Error",
          description="An internal error has occurred, please try again later",
          colour=discord.Colour.red()
        )
  await interaction.response.send_message(embed=embed)

@bot.tree.command(name="whyjerome")
async def whyjerome(interaction: discord.Interaction):
  embed = discord.Embed(
      title="Why Jerome:",
      description='The /jerome command gives a random quote',
      colour=discord.Colour.random()
  )
  embed.set_author(name='Jerome', icon_url=bot.user.display_avatar.url) # type: ignore
  embed.set_footer(text="/mini ♥ /jerome ")
  await interaction.response.send_message(embed=embed)



bot.run(os.getenv("TOKEN")) # type: ignore
