import discord
from bot.types import EmbedPage
from .components import PageSelector


class VPages(discord.ui.View):
    """Paginates some information"""
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list[EmbedPage],
            current_page: int = 0,
            timeout: float = None,
    ):
        super().__init__(timeout=timeout)
        self.og_interaction = interaction
        self.pages = pages
        self.current_page = current_page

        self.add_item(PageSelector(
            self.pages,
            self.current_page,
            self.on_page_select,
            owner=interaction.user,
        ))

    async def on_page_select(
            self,
            interaction: discord.Interaction,
            page_idx: int,
    ) -> None:
        new_page = self.pages[page_idx]
        await interaction.response.defer(thinking=False)

        content = await new_page[2].content()
        embeds = await new_page[2].embeds()
        await self.og_interaction.edit_original_response(
            content=content,
            embeds=embeds if embeds else [],
            view=VPages(
                self.og_interaction,
                self.pages,
                current_page=page_idx,
                timeout=self.timeout,
            )
        )
