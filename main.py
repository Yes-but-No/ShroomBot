from __future__ import annotations

import discord

from bot import ShroomBot, get_config_from_env

config = get_config_from_env()

bot = ShroomBot(
  config=config,
  help_command=None,
  intents=discord.Intents.all(),
  owner_ids=(751768586699276342, 759195783597129760)
)

bot.run(root_logger=True)
