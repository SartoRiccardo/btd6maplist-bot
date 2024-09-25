import discord
from .components import OwnerButton
from .modals import MSelectPage
from bot.types import RequestPagesCb, PageContentBuilderCb
from bot.utils.formulas import get_page_idxs
from bot.utils.discord import composite_views
from typing import Any


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
            additional_views: list[discord.ui.View] | None = None,
            list_key: str = "entries",
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
        :param list_key: Key to access the list in the payload.
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

        self.list_key = list_key
        self.additional_views = additional_views

        if total_pages == 1:
            return

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

    def get_needed_rows(self, page: int, saved_pages: dict[int, dict | list]) -> list[Any]:
        needed = []
        start_idx, end_idx, req_page_start, req_page_end = get_page_idxs(page, self.items_page, self.items_page_srv)
        for srv_page_idx in range(req_page_start, req_page_end + 1):
            srv_page = saved_pages[srv_page_idx]

            entry_sidx = start_idx % self.items_page_srv
            count = min(len(srv_page[self.list_key]), entry_sidx + end_idx - start_idx + 1)
            for i in range(entry_sidx, count):
                needed.append(srv_page[self.list_key][i])
            start_idx += count - entry_sidx

        return needed

    async def go_to_page(self, page: int) -> None:
        _si, _ei, req_page_start, req_page_end = get_page_idxs(page, self.items_page, self.items_page_srv)
        idx_to_request = [
            pg for pg in range(req_page_start, req_page_end + 1)
            if pg not in self.pages_saved
        ]

        saved_pages = self.pages_saved
        if self.request_cb:
            saved_pages = await self.request_cb(
                [pg for pg in idx_to_request]
            )
            saved_pages = {
                **self.pages_saved,
                **saved_pages,
            }

        entries = self.get_needed_rows(page, saved_pages)
        content = self.message_build_cb(entries)
        views = [
            VPaginateList(
                self.og_interaction,
                self.total_pages,
                page,
                saved_pages,
                self.items_page,
                self.items_page_srv,
                self.request_cb,
                self.message_build_cb,
                additional_views=self.additional_views,
                timeout=self.timeout,
                list_key=self.list_key,
            )
        ]
        if self.additional_views:
            views += self.additional_views

        await self.og_interaction.edit_original_response(
            content=content if isinstance(content, str) else None,
            embed=content if isinstance(content, discord.Embed) else None,
            view=composite_views(*views),
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
