from __future__ import annotations

from typing import TYPE_CHECKING

from discord.app_commands import check

from bot.errors import UnderMaintenance

if TYPE_CHECKING:
  from discord import Interaction

  from bot import ShroomBot


def under_maintenance():
  def predicate(interaction: Interaction[ShroomBot]):
    if not interaction.client.under_maintenance:
      return True
    raise UnderMaintenance("bot is under maintenance, try again later")
  
  return check(predicate)