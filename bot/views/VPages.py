import discord
from bot.types import EmbedPage
from .components import PageSelector
from bot.utils.discordutils import composite_views


class VPages(discord.ui.View):
    """Paginates some information"""
    def __init__(
            self,
            interaction: discord.Interaction,
            pages: list[EmbedPage],
            current_page: int = 0,
            placeholder: str = "Other map info",
            timeout: float = None,
            autoload: bool = True,
    ):
        super().__init__(timeout=timeout)
        self.og_interaction = interaction
        self.pages = pages
        self.current_page = current_page
        self.placeholder = placeholder

        if autoload:
            self.load_items()

    def load_items(self):
        self.add_item(PageSelector(
            self.pages,
            self.current_page,
            self.on_page_select,
            placeholder=self.placeholder,
            owner=self.og_interaction.user,
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
        updated_view = [VPages(
            self.og_interaction,
            self.pages,
            current_page=page_idx,
            timeout=self.timeout,
        )]
        if page_view := await new_page[2].view():
            updated_view.insert(0, page_view)
        await self.og_interaction.edit_original_response(
            content=content,
            embeds=embeds if embeds else [],
            view=composite_views(*updated_view),
        )

