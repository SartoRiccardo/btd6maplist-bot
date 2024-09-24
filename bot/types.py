import discord
from typing import Literal, Callable, Awaitable


Format = Literal["Current Version"]
LbType = Literal["Points", "LCCs"]
ExpertDifficulty = Literal["Casual Expert", "Medium Expert", "High Expert", "True Expert"]
MapPlacement = Literal[
    "Maplist / Top 3",
    "Maplist / Top 10",
    "Maplist / #11 ~ 20",
    "Maplist / #21 ~ 30",
    "Maplist / #31 ~ 40",
    "Maplist / #41 ~ 50",
    "Experts / Casual Expert",
    "Experts / Casual-Medium",
    "Experts / Medium Expert",
    "Experts / Medium-High",
    "Experts / High Expert",
    "Experts / High-True",
    "Experts / True Expert",
]

# emoji, page name, content, embed
EmbedPage = tuple[str, str, str | None, list[discord.Embed] | None]

RequestPagesCb = Callable[[list[int]], Awaitable[dict[int, dict]]]
PageContentBuilderCb = Callable[[int, dict[int, dict]], str | discord.Embed]
SubmitMapModalCb = Callable[[discord.Interaction, str | None], Awaitable[None]]
SubmitRunModalCb = Callable[[discord.Interaction, str | None, str | None, int | None], Awaitable[None]]
