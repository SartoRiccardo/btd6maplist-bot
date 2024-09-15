import discord
from typing import Literal, Callable, Awaitable


Format = Literal["Current Version"]
LbType = Literal["Points", "LCCs"]

# emoji, page name, content, embed
EmbedPage = tuple[str, str, str | None, list[discord.Embed] | None]

RequestPagesCb = Callable[[list[int]], Awaitable[dict[int, dict]]]
LbBuilderCb = Callable[[int, dict[int, dict]], str]
