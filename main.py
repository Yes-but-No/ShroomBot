from __future__ import annotations

import os

import discord
from discord.ext.commands import when_mentioned_or

from bot import ShroomBot

DATABASE_URL = os.getenv("MONGO_URL")

if DATABASE_URL is None:
  url = "localhost"
else:
  url = DATABASE_URL

bot = ShroomBot(
  mongo_url=url,
  command_prefix=when_mentioned_or("$"),
  help_command=None,
  intents=discord.Intents.all(),
  owner_ids=(751768586699276342, 759195783597129760)
)

bot.run(os.getenv("TOKEN")) # type: ignore
