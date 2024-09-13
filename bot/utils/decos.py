import discord
import inspect
from typing import Callable
from functools import wraps


def autodoc(command: Callable):
    """Automatically documents some parameters."""
    documented_fields = {
        "hide": (None, "Hides the message"),
        "map_id": ("map", "The map's code. Can also be its name, an alias or its list position."),
    }
    cmd_args = inspect.getfullargspec(command).args
    renames = {}
    descriptions = {}
    for argname in cmd_args:
        if argname not in documented_fields:
            continue

        if documented_fields[argname][0]:
            renames[argname] = documented_fields[argname][0]
        if documented_fields[argname][1]:
            descriptions[argname] = documented_fields[argname][1]

    @discord.app_commands.rename(**renames)
    @discord.app_commands.describe(**descriptions)
    @wraps(command)
    async def wrapper(*args, **kwargs):
        await command(*args, **kwargs)
    return wrapper
