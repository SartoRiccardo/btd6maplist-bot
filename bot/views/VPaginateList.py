import discord
from .components import OwnerButton
from .modals import MSelectPage
from bot.types import RequestPagesCb, PageContentBuilderCb
from bot.utils.formulas import get_page_idxs


class VPaginateList(discord.ui.View):
    """Paginates a list gotten from a server"""
    def __init__(
            self,
            interaction: discord.Interaction,
            total_pages: int,
            current_page: int,
            pages_saved: dict[int, dict | list],
            items_page: int,
            items_page_srv: int,
            request_cb: RequestPagesCb | None,
            message_build_cb: PageContentBuilderCb,
            timeout: float = None,
    ):
        """
        :param interaction: Original interaction to edit
        :param total_pages: Total number of pages (Discord)
        :param current_page: Page the user is on
        :param pages_saved: Number of page and contents of the page (API)
        :param items_page: Items per page (Discord)
        :param items_page_srv: Items per page (API)
        :param request_cb: Awaitable that updates pages_saved, is called if more pages are needed.
        :param message_build_cb: Callback that returns a string that will be outputted
        """
        super().__init__(timeout=timeout)
        self.og_interaction = interaction
        self.total_pages = total_pages
        self.current_page = current_page

        self.pages_saved = pages_saved
        self.items_page = items_page
        self.items_page_srv = items_page_srv
        self.request_cb = request_cb
        self.message_build_cb = message_build_cb

        self.add_item(OwnerButton(
            self.og_interaction.user,
            self.ff_back,
            style=discord.ButtonStyle.blurple,
            emoji="⏮️",
            disabled=self.current_page <= 1,
        ))
        self.add_item(OwnerButton(
            self.og_interaction.user,
            self.page_back,
            style=discord.ButtonStyle.blurple,
            emoji="◀️",
            disabled=self.current_page <= 1,
        ))

        self.add_item(OwnerButton(
            self.og_interaction.user,
            self.modal_select_page,
            style=discord.ButtonStyle.gray,
            label=f"{min(self.current_page, self.total_pages)} / {self.total_pages}",
        ))

        self.add_item(OwnerButton(
            self.og_interaction.user,
            self.page_next,
            style=discord.ButtonStyle.blurple,
            emoji="▶️",
            disabled=self.current_page >= self.total_pages,
        ))
        self.add_item(OwnerButton(
            self.og_interaction.user,
            self.ff_next,
            style=discord.ButtonStyle.blurple,
            emoji="⏭️",
            disabled=self.current_page >= self.total_pages,
        ))

    async def go_to_page(self, page: int) -> None:
        _si, _ei, req_page_start, req_page_end = get_page_idxs(page, self.items_page, self.items_page_srv)
        idx_to_request = [
            pg for pg in range(req_page_start, req_page_end + 1)
            if pg not in self.pages_saved
        ]

        lb_pages = self.pages_saved
        if self.request_cb:
            lb_pages = await self.request_cb(
                [pg for pg in idx_to_request]
            )
            lb_pages = {
                **self.pages_saved,
                **lb_pages,
            }

        content = self.message_build_cb(page, lb_pages)
        await self.og_interaction.edit_original_response(
            content=content if isinstance(content, str) else None,
            embed=content if isinstance(content, discord.Embed) else None,
            view=VPaginateList(
                self.og_interaction,
                self.total_pages,
                page,
                lb_pages,
                self.items_page,
                self.items_page_srv,
                self.request_cb,
                self.message_build_cb,
                timeout=self.timeout,
            ),
        )

    async def modal_select_page(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            MSelectPage(self.total_pages, self.go_to_page)
        )

    async def ff_back(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=False)
        await self.go_to_page(1)

    async def page_back(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=False)
        await self.go_to_page(self.current_page-1)

    async def page_next(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=False)
        await self.go_to_page(self.current_page+1)

    async def ff_next(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=False)
        await self.go_to_page(self.total_pages)
