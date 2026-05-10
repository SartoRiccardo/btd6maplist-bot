import asyncio
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.emojis import EmjPlacements
from bot.utils.decos import autodoc
from bot.types import Format, LbType
from bot.utils.requests.maplist import get_leaderboard
from bot.exceptions import MaplistResNotFound
from bot.views import VPaginateList


row_template = "{emoji} `{name: <20}`  |  `{score: <5,}`"
items_page = 20
placements_emojis = {
    1: f"  {EmjPlacements.top1} ",
    2: f"  {EmjPlacements.top2} ",
    3: f"  {EmjPlacements.top3} ",
}


class LeaderboardCog(CogBase):
    help_descriptions = {
        "leaderboard": "Get the Maplist leaderboard. You can choose format and page.",
    }

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @discord.app_commands.command(
        name="leaderboard",
        description="Get the Maplist leaderboard",
    )
    @discord.app_commands.rename(game_format="list")
    @discord.app_commands.describe(
        lb_type="The type of leaderboard points",
    )
    @autodoc
    async def cmd_leaderboard(
            self,
            interaction: discord.Interaction,
            page: int = 1,
            game_format: Format = "Maplist",
            lb_type: LbType = "Points",
            hide: bool = False,
    ):
        if page <= 0:
            return await interaction.response.send_message(
                content="You can't have a negative page!",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=hide)

        try:
            lb_pages = await self.request_pages(lb_type, game_format, [page])
        except MaplistResNotFound:
            return await interaction.edit_original_response(
                content=f"❌ The {lb_type} leaderboard for the {game_format} does not exist!",
            )

        if lb_pages[page]["meta"]["total"] == 0:
            return await interaction.edit_original_response(
                content="❌ No entries!\n"
                        "-# Maybe your page number was too big?"
            )

        client_pages = lb_pages[page]["meta"]["last_page"]
        view = VPaginateList(
            interaction,
            client_pages,
            page,
            lb_pages,
            items_page,
            items_page,
            lambda pages: self.request_pages(lb_type, game_format, pages),
            self.create_lb_message,
            list_key="data",
        )
        await interaction.edit_original_response(
            content=self.create_lb_message(view.get_needed_rows(page, lb_pages)),
            view=view,
        )

    @staticmethod
    async def request_pages(
            lb_type: LbType,
            game_format: Format,
            pages: list[int],
    ) -> dict[int, dict]:
        lb_data = await asyncio.gather(*[
            get_leaderboard(lb_type, game_format, pg, per_page=items_page)
            for pg in pages
        ])
        return {pg: lb_data[i] for i, pg in enumerate(pages)}

    @staticmethod
    def create_lb_message(entries: list[dict]) -> str:
        rows = [
            "User                                                   |    Points",
            "———————————————-   +   —————",
        ]
        for entry in entries:
            plcmt = placements_emojis.get(entry["placement"], f"`{entry['placement']: >3}`")
            rows.append(row_template.format(
                emoji=plcmt,
                name=entry["user"]["name"],
                score=entry["score"] if not entry["score"].is_integer else int(entry["score"]),
            ))

        return "\n".join(rows)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
