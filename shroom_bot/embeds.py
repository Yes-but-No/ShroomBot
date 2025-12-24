from discord import Colour, Embed


def farm_already_exists() -> Embed:
    return Embed(
        title="Farm already exists!",
        description="Your server already has a farm set up, if you wish to change the farm channel, use `/setchannel` instead",
        colour=Colour.red(),
    )


def change_farm_channel_not_set_up() -> Embed:
    return Embed(
        title="Farm not set up!",
        description="Your server has not set up the farm yet, use `/setup` instead",
        colour=Colour.red(),
    )


def farm_not_set_up() -> Embed:
    return Embed(
        title="Farm not set up!",
        description="Use `/setup` to setup your server and start farming!",
        colour=Colour.red(),
    )


def account_not_found() -> Embed:
    return Embed(
        title="Account not found!",
        description="User has not started farming yet",
        colour=Colour.red(),
    )


def cannot_farm() -> Embed:
    return Embed(
        title="You cannot farm mushrooms now",
        description="You can only farm mushrooms one at a time",
        colour=Colour.red(),
    )


def daily_goal_reached() -> Embed:
    return Embed(
        title="Daily goal reached!",
        description="All contributors have been awarded double Shroom Tokens!",
        colour=Colour.green(),
    )


def under_maintenance() -> Embed:
    return Embed(
        title="Bot is under maintenance",
        description="Bot is currently under maintenance, please try again later",
        colour=Colour.red(),
    )


def farm_create_success(channel_id: int) -> Embed:
    return Embed(
        title="Success!",
        description=f"Farm created successfully, send a 🍄 in <#{channel_id}> to start farming!",
        colour=Colour.green(),
    )


def channel_change_success(channel_id: int) -> Embed:
    return Embed(
        title="Success!",
        description=f"The farm channel has been successfully changed to <#{channel_id}>",
        colour=Colour.green(),
    )


def set_daily_goal_success(goal: int) -> Embed:
    return Embed(
        title="Success!",
        description=(
            f"The daily goal has been successfully changed to `{goal}`\n"
            "If you have already farmed mushrooms today, the daily goal will only apply tomorrow!"
        ),
        colour=Colour.green(),
    )


def error_message(message: str) -> Embed:
    return Embed(
        title="Error",
        description=message,
        colour=Colour.red(),
    )


def ranked_up(name: str, new_rank: str) -> Embed:
    return Embed(
        title=f"{name} ranked up!",
        description=f"Your rank is now `{new_rank}`!",
        colour=Colour.green(),
    )


def coming_back_soon() -> Embed:
    return Embed(
        title="Coming back soon!",
        description="This feature is coming back soon, stay tuned!",
        colour=Colour.blue(),
    )
