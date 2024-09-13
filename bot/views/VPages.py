import discord
from bot.types import EmbedPage
from bot.views.components import PageSelector


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
        ))

    async def on_page_select(
            self,
            interaction: discord.Interaction,
            page_idx: int,
    ) -> None:
        if interaction.user.id != self.og_interaction.user.id:
            await interaction.response.send_message(
                content=f"The command was executed by <@{self.og_interaction.user.id}>. "
                        "Run the command yourself!",
                ephemeral=True,
            )
            return

        new_page = self.pages[page_idx]
        await interaction.response.send_message(
            content=f"Showing **{new_page[0]} {new_page[1]}**",
            ephemeral=True,
        )

        await self.og_interaction.edit_original_response(
            content=new_page[2],
            embed=new_page[3],
            view=VMapPages(
                self.og_interaction,
                self.pages,
                current_page=page_idx,
                timeout=self.timeout,
            )
        )
