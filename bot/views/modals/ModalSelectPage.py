import discord
from .ModalBase import ModalBase
from typing import Awaitable, Callable


class MSelectPage(ModalBase, title="Select a Page"):
    page = discord.ui.TextInput(
        label="New Page",
        placeholder="Page number...",
        max_length=2,
        required=True,
    )

    def __init__(self, max_page: int, submit_cb: Callable[[int], Awaitable[None]]):
        super().__init__()
        self.max_page = max_page
        self.submit_cb = submit_cb

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.page.value.isnumeric() and 0 < int(self.page.value) <= self.max_page

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False)
        await self.submit_cb(int(self.page.value))
