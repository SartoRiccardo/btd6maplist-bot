import asyncio
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.emojis import EmjPlacements
from bot.utils.decos import autodoc
from bot.types import Format, LbType
from bot.utils.requests.maplist import get_leaderboard


row_template = "{emoji} `{name: <20}`  |  `{score: <5,}`"
items_page = 3
items_page_srv = 10
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

        _si, _ei, req_page_start, req_page_end = self.get_req_pages(page)
        lb_data = await asyncio.gather(*[
            get_leaderboard(lb_type, game_format, pg)
            for pg in range(req_page_start, req_page_end+1)
        ])
        lb_pages = {
            pg: lb_data[pg-req_page_start]
            for pg in range(req_page_start, req_page_end+1)
        }

        await interaction.edit_original_response(
            content=self.create_lb_message(page, lb_pages),
            view=None,
        )

    @staticmethod
    def get_req_pages(page) -> tuple[int, int, int, int]:
        start_idx = (page-1) * items_page
        end_idx = page * items_page - 1
        req_page_start = start_idx // items_page_srv + 1
        req_page_end = end_idx // items_page_srv + 1
        return start_idx, end_idx, req_page_start, req_page_end

    @staticmethod
    def create_lb_message(
            page: int,
            lb_pages: dict[int, dict],
    ) -> str:
        rows = [
            "User                                                   |    Points",
            "———————————————-   +   —————",
        ]
        start_idx, end_idx, req_page_start, req_page_end = LeaderboardCog.get_req_pages(page)
        for srv_page_idx in range(req_page_start, req_page_end+1):
            srv_page = lb_pages[srv_page_idx]

            entry_sidx = start_idx % items_page_srv
            count = min(items_page_srv, entry_sidx + end_idx-start_idx + 1)
            for i in range(entry_sidx, count):
                entry = srv_page["entries"][i]
                plcmt = placements_emojis.get(entry["position"], f"`{entry['position']: <3}`")
                rows.append(row_template.format(
                    emoji=plcmt,
                    name=entry["user"]["name"],
                    score=entry["score"],
                ))
            start_idx += count - entry_sidx

        return "\n".join(rows)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
