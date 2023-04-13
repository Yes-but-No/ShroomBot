"""
Errors raised by the bot
"""

from discord.app_commands import AppCommandError

class UnderMaintenance(AppCommandError):
  """Raised when the check for bot being under maintenance fails"""
  pass