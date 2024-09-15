import asyncio
import math
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.emojis import EmjPlacements
from bot.utils.decos import autodoc
from bot.types import Format, LbType
from bot.utils.requests.maplist import get_leaderboard
from bot.views import VPaginateList
from bot.utils.formulas import get_page_idxs


row_template = "{emoji} `{name: <20}`  |  `{score: <5,}`"
items_page = 20
items_page_srv = 50
placements_emojis = {
    1: f"  {EmjPlacements.top1} ",
    2: f"  {EmjPlacements.top2} ",
    3: f"  {EmjPlacements.top3} ",
}


class LeaderboardCog(CogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @discord.app_commands.command(
        name="leaderboard",
        description="Get the Maplist leaderboard",
    )
    @discord.app_commands.describe(
        lb_type="The type of leaderboard points",
    )
    @autodoc
    async def cmd_leaderboard(
            self,
            interaction: discord.Interaction,
            page: int = 1,
            game_format: Format = "Current Version",
            lb_type: LbType = "Points",
            hide: bool = False,
    ):
        if page <= 0:
            return await interaction.response.send_message(
                content="You can't have a negative page!",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=hide)

        _si, _ei, req_page_start, req_page_end = get_page_idxs(page, items_page, items_page_srv)
        lb_pages = await self.request_pages(
            lb_type,
            game_format,
            [pg for pg in range(req_page_start, req_page_end+1)]
        )

        if lb_pages[req_page_start]["pages"] == 0:
            return await interaction.edit_original_response(
                content="❌ No entries!\n"
                        "-# Maybe your page number was too big?"
            )

        client_pages = math.ceil(lb_pages[req_page_start]["total"] / items_page)
        await interaction.edit_original_response(
            content=self.create_lb_message(page, lb_pages),
            view=VPaginateList(
                interaction,
                client_pages,
                page,
                lb_pages,
                items_page,
                items_page_srv,
                lambda pages: self.request_pages(lb_type, game_format, pages),
                self.create_lb_message,
            ),
        )

    @staticmethod
    async def request_pages(
            lb_type: LbType,
            game_format: Format,
            pages: list[int],
    ) -> dict[int, dict]:
        lb_data = await asyncio.gather(*[
            get_leaderboard(lb_type, game_format, pg)
            for pg in pages
        ])
        return {pg: lb_data[i] for i, pg in enumerate(pages)}

    @staticmethod
    def create_lb_message(
            page: int,
            lb_pages: dict[int, dict],
    ) -> str:
        rows = [
            "User                                                   |    Points",
            "———————————————-   +   —————",
        ]
        start_idx, end_idx, req_page_start, req_page_end = get_page_idxs(page, items_page, items_page_srv)
        for srv_page_idx in range(req_page_start, req_page_end+1):
            srv_page = lb_pages[srv_page_idx]

            entry_sidx = start_idx % items_page_srv
            count = min(len(srv_page["entries"]), entry_sidx + end_idx-start_idx + 1)
            for i in range(entry_sidx, count):
                entry = srv_page["entries"][i]
                plcmt = placements_emojis.get(entry["position"], f"`{entry['position']: >3}`")
                rows.append(row_template.format(
                    emoji=plcmt,
                    name=entry["user"]["name"],
                    score=entry["score"] if not entry["score"].is_integer else int(entry["score"]),
                ))
            start_idx += count - entry_sidx

        return "\n".join(rows)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))