import discord
from bot.types import EmbedPage
from typing import Callable


class PageSelector(discord.ui.Select):
    def __init__(
            self,
            pages: list[EmbedPage],
            current_idx: int,
            callback: Callable,
            placeholder: str = "Other map info",
            owner: discord.User | None = None,
    ):
        self.pages = pages
        self.callback_func = callback
        self.current_idx = current_idx
        self.owner = owner
        options = [
            discord.SelectOption(emoji=pg[0], label=pg[1])
            for i, pg in enumerate(self.pages)
            if i != self.current_idx
        ]

        super().__init__(
            placeholder=placeholder,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            idx = next(i for i, pg in enumerate(self.pages) if pg[1] == self.values[0])
            await self.callback_func(interaction, idx)
        except StopIteration:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        should_handle = self.owner is None or self.owner.id == interaction.user.id
        if not should_handle:
            await interaction.response.send_message(
                content=f"The command was executed by <@{self.owner.id}>. "
                        "Run the command yourself!",
                ephemeral=True,
            )

        return should_handle
