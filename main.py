from __future__ import annotations

import discord

from shroom_bot import ShroomBot, get_bot_config

if __name__ == "__main__":
    discord.utils.setup_logging(root=True)

    config = get_bot_config()

    bot = ShroomBot(
        config=config, intents=discord.Intents.all(), owner_id=751768586699276342
    )

    bot.run(log_handler=None)
