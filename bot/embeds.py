import discord

FARM_ALREADY_EXISTS = discord.Embed(
  title="Farm already exists!",
  description="Your server already has a farm set up, if you wish to change the farm channel, use `/setchannel` instead",
  colour=discord.Colour.red()
)

CHANGE_FARM_CHANNEL_NOT_SET_UP = discord.Embed(
  title="Farm not set up!",
  description="Your server has not set up the farm yet, use `/setup` instead",
  colour=discord.Colour.red()
)

FARM_NOT_SET_UP = discord.Embed(
  title="Farm not set up!",
  description="Use `/setup` to setup your server and start farming!",
  colour=discord.Colour.red()
)

ACCOUNT_NOT_FOUND = discord.Embed(
  title="Account not found!",
  description="User has not started farming yet",
  colour=discord.Colour.red()
)

CANNOT_FARM = discord.Embed(
  title="You cannot farm mushrooms now",
  description="You can only farm mushrooms one at a time",
  colour=discord.Colour.red()
)

DAILY_GOAL_REACHED = discord.Embed(
  title="Daily goal reached!",
  description="All contributors have been awarded double Shroom Tokens!",
  colour=discord.Colour.green()
)

def FARM_CREATE_SUCCESS(channel_id: int) -> discord.Embed:
  return discord.Embed(
    title="Success!",
    description=f"Farm created successfully, send a 🍄 in <#{channel_id}> to start farming!",
    colour=discord.Colour.green()
  )

def CHANNEL_CHANGE_SUCCESS(channel_id: int) -> discord.Embed:
  return discord.Embed(
    title="Success!",
    description=f"The farm channel has been successfully changed to <#{channel_id}>",
    colour=discord.Colour.green()
  )

def SET_DAILY_GOAL_SUCCESS(goal: int) -> discord.Embed:
  return discord.Embed(
    title="Success!",
    description=(
      f"The daily goal has been successfully changed to `{goal}`\n"
      "If you have already farmed mushrooms today, the daily goal will only apply tomorrow!"
    ),
    colour=discord.Colour.green()
  )

def ERROR_MESSAGE(msg: str) -> discord.Embed:
  return discord.Embed(
      title="Error!",
      description=msg,
      colour=discord.Colour.red()
  )

def RANKED_UP(name: str, new_rank: str) -> discord.Embed:
  return discord.Embed(
    title=f"{name} ranked up!",
    description=f"Your rank is now `{new_rank}`!",
    colour=discord.Colour.green()
  )