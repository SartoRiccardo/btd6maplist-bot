import discord
from bot.types import EmbedPage
from typing import Callable


class PageSelector(discord.ui.Select):
    def __init__(
            self,
            pages: list[EmbedPage],
            current_idx: int,
            callback: Callable,
    ):
        self.pages = pages
        self.callback_func = callback
        self.current_idx = current_idx
        options = [
            discord.SelectOption(emoji=pg[0], label=pg[1])
            for i, pg in enumerate(self.pages)
            if i != self.current_idx
        ]

        super().__init__(
            placeholder="Other map info",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            idx = next(i for i, pg in enumerate(self.pages) if pg[1] == self.values[0])
            await self.callback_func(interaction, idx)
        except StopIteration:
            pass
