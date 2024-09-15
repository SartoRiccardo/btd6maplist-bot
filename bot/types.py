import discord
from typing import Literal


Format = Literal["Current Version"]
LbType = Literal["Points", "LCCs"]

# emoji, page name, content, embed
EmbedPage = tuple[str, str, str | None, list[discord.Embed] | None]
