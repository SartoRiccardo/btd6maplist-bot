import discord
from bot.utils.models import MessageContent
from typing import Literal, Callable, Awaitable, Any


Format = Literal["Maplist", "Expert List"]
LbType = Literal["Points", "LCCs", "No Optimal Hero", "Black Border"]
ExpertDifficulty = Literal["Casual Expert", "Medium Expert", "High Expert", "True Expert", "Extreme Expert"]
BotbDifficulty = Literal["Beginner", "Intermediate", "Advanced", "Expert"]
NostalgiaPackGame = Literal[
    "Bloons TD 1/2/3",
    "Bloons TD iOS/PSN/DSi",
    "Bloons TD 4",
    "Bloons TD 5",
    "Bloons TD Battles",
    "Bloons Monkey City",
    "Bloons Adventure Time TD",
    "Bloons TD Battles 2",
]
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

# emoji, page name, content
EmbedPage = tuple[str | None, str, MessageContent]

RequestPagesCb = Callable[[list[int]], Awaitable[dict[int, dict]]]
PageContentBuilderCb = Callable[[list[Any]], str | discord.Embed]
SubmitMapModalCb = Callable[[discord.Interaction, str | None], Awaitable[None]]
SubmitRunModalCb = Callable[[discord.Interaction, str | None, list[str] | None, int | None], Awaitable[None]]
BuildRunModalCb = Callable[[int], "bot.views.modals.MRunSubmission"]
SelectFormatCb = Callable[[discord.Interaction, int], Awaitable[None]]
