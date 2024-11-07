import discord
from bot.utils.models import MessageContent
from typing import Literal, Callable, Awaitable, Any


Format = Literal["Maplist", "Expert List"]
LbType = Literal["Points", "LCCs", "No Optimal Hero", "Black Border"]
ExpertDifficulty = Literal["Casual Expert", "Medium Expert", "High Expert", "True Expert", "Extreme Expert"]
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
    "Experts / True-Extreme",
    "Experts / Extreme Expert",
]

# emoji, page name, content, embed
EmbedPage = tuple[str, str, MessageContent]

RequestPagesCb = Callable[[list[int]], Awaitable[dict[int, dict]]]
PageContentBuilderCb = Callable[[list[Any]], str | discord.Embed]
SubmitMapModalCb = Callable[[discord.Interaction, str | None], Awaitable[None]]
SubmitRunModalCb = Callable[[discord.Interaction, str | None, list[str] | None, int | None], Awaitable[None]]
