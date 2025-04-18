import asyncio
import math
import re
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.formulas import get_page_idxs
from bot.utils.requests.maplist import (
    get_maplist_user,
    get_user_completions,
    set_oak,
    get_formats,
    get_banner_medals_url,
)
from bot.utils.requests.ninjakiwi import get_btd6_user
from bot.views import VPages, VPaginateList
from bot.utils.models import MessageContent, LazyMessageContent
from bot.exceptions import MaplistResNotFound
from config import EMBED_CLR, WEB_BASE_URL
from bot.utils.emojis import EmjMedals, EmjIcons, EmjPlacements, EmjMisc


empty_profile = {
    "list_stats": [],
    "created_maps": [],
    "medals": {
        "wins": 0,
    },
    "avatarURL": "https://static-api.nkstatic.com/appdocs/4/assets/opendata/db32af61df5646951a18c60fe0013a31_ProfileAvatar01.png",
    "bannerURL": "https://static-api.nkstatic.com/appdocs/4/assets/opendata/bbd8e1412f656b91db7df7aabbc1598b_TeamsBannerDeafult.png",
}
placements_emojis = {
    1: EmjPlacements.top1,
    2: EmjPlacements.top2,
    3: EmjPlacements.top3,
}


class UserCog(CogBase):
    help_descriptions = {
        "profile": "Check an user's (or your own) profile!",
        "oak": "Verify your BTD6 profile!",
    }

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @discord.app_commands.command(
        name="profile",
        description="Check an user's Maplist stats",
    )
    @discord.app_commands.describe(user="The user to check")
    @autodoc
    async def cmd_profile(
            self,
            interaction: discord.Interaction,
            user: discord.User = None,
            hide: bool = False,
    ):
        if user == self.bot.user:
            return await interaction.response.send_message(
                content="That's me!",
                ephemeral=True,
            )
        await self.send_user_profile(interaction, interaction.user if user is None else user, hide)

    @staticmethod
    async def fetch_user(user_id: int):
        try:
            return await get_maplist_user(user_id)
        except MaplistResNotFound:
            return empty_profile

    async def send_user_profile(
            self,
            interaction: discord.Interaction,
            user: discord.User,
            hide: bool = False,
    ):
        await interaction.response.defer(ephemeral=hide)

        profile, formats = await asyncio.gather(
            self.fetch_user(user.id),
            get_formats(),
        )

        pages = [
            ("ℹ️", "User Overview", self.get_user_message(interaction, user, profile, formats)),
        ]

        views_to_load = []
        if profile["medals"]["wins"] > 0:
            views_to_load.append(
                VPages(interaction, pages, placeholder="Other user info", current_page=len(pages), autoload=False)
            )
            pages.append((
                EmjMedals.win, "Completions",
                self.get_completions_message(interaction, user, views_to_load[-1]),
            ))

        for view in views_to_load:
            view.load_items()

        pages_view = None
        if len(pages) > 1:
            pages_view = VPages(interaction, pages, placeholder="Other user info")

        await interaction.edit_original_response(
            embeds=await pages[0][2].embeds(),
            view=pages_view,
        )

    @staticmethod
    def get_completions_message(
            interaction: discord.Interaction,
            user: discord.User,
            pages_view: VPages,
    ) -> MessageContent:
        items_page = 12
        items_page_srv = 50
        _si, _ei, req_page_start, req_page_end = get_page_idxs(1, items_page, items_page_srv)

        async def request_completions(pages: list[int]):
            lb_data = await asyncio.gather(*[
                get_user_completions(user.id, pg)
                for pg in pages
            ])
            return {pg: lb_data[i] for i, pg in enumerate(pages)}

        def build_message(entries: list[dict]) -> str:
            if len(entries) == 0:
                return f"## {user.display_name} — Completions\n\n" \
                       f"-# Not much going on here... go play the game!"

            row_template = "{}  ~  {}  |  {}\n"
            content = f"## {user.display_name} — Completions\n" \
                      "Format ~ Medals   |  Map\n" \
                      "—————————  + —————————\n"
            medal_spots = 3
            for i, entry in enumerate(entries):
                format_emj = EmjIcons.format(entry["format"])
                comp_medals = []
                if entry["format"] <= 50 and entry["no_geraldo"]:
                    comp_medals.append(EmjMedals.no_opt_hero)
                if entry["current_lcc"]:
                    comp_medals.append(EmjMedals.lcc)
                comp_medals.append(EmjMedals.bb if entry["black_border"] else EmjMedals.win)
                for _ in range(len(comp_medals), medal_spots):
                    comp_medals.insert(0, EmjMisc.blank)

                map_name = entry["map"]["name"]
                if i+1 < len(entries) and entry["map"]["code"] == entries[i+1]["map"]["code"]:
                    map_name = "↓     ↓     ↓     ↓"
                content += row_template.format(format_emj, " ".join(comp_medals), map_name)
            return content.strip()

        async def load_message() -> MessageContent:
            pages_to_req = [pg for pg in range(req_page_start, req_page_end+1)]
            comp_pages = await request_completions(pages_to_req)

            client_pages = math.ceil(comp_pages[req_page_start]["total"] / items_page)
            view = VPaginateList(
                interaction,
                client_pages,
                1,
                comp_pages,
                items_page,
                items_page_srv,
                request_completions,
                build_message,
                additional_views=[pages_view],
                list_key="completions",
            )
            return MessageContent(
                content=view.message_on_page(1),
                view=view,
            )

        return LazyMessageContent(load_message)

    @staticmethod
    def get_user_message(
            interaction: discord.Interaction,
            user: discord.User,
            profile: dict,
            formats: list[dict],
    ) -> MessageContent:
        description = ""
        if len(profile["created_maps"]):
            description += f"- **Maps Created:** {len(profile['created_maps'])}\n"
        # Never miss a chance to be cooler than others
        if user.id == 1077309729942024302:
            description += "- **Bots Created:** This one and some others\n" \
                           f"- **Websites Created:** [{WEB_BASE_URL.split('//', 1)[1]}]({WEB_BASE_URL})"

        something = len(description) > 0

        embed = discord.Embed(
            title=user.display_name,
            color=EMBED_CLR,
            description=description.strip(),
        )
        if profile["medals"]["wins"] > 0:
            banner_url = profile["bannerURL"] if profile["bannerURL"] else empty_profile["bannerURL"]
            embed.set_image(url=get_banner_medals_url(banner_url, profile["medals"]))
        elif profile["bannerURL"] and profile != empty_profile:
            embed.set_image(url=profile["bannerURL"])

        embed.set_thumbnail(url=profile["avatarURL"] if profile["avatarURL"] else empty_profile["avatarURL"])

        for stats in sorted(profile["list_stats"], key=lambda x: x["format_id"]):
            format_data = next(f for f in formats if f["id"] == stats["format_id"])
            if format_data["hidden"]:
                continue

            something = True
            prf = stats["stats"]
            description = f'**Score:** {int(prf["points"]) if prf["points"].is_integer() else prf["points"]}pt ' + \
                          placements_emojis.get(prf["pts_placement"], f'(#{prf["pts_placement"]})')
            if prf["lccs"]:
                amount = int(prf["lccs"]) if prf["lccs"].is_integer() else prf["lccs"]
                description += f'\n- {EmjMedals.lcc} {amount} LCCs ' + \
                               placements_emojis.get(prf["lccs_placement"], f'(#{prf["lccs_placement"]})')
            if prf["no_geraldo"]:
                amount = int(prf["no_geraldo"]) if prf["lccs"].is_integer() else prf["no_geraldo"]
                description += f'\n- {EmjMedals.no_opt_hero} {amount} No Optimal Hero runs ' + \
                               placements_emojis.get(prf["lccs_placement"], f'(#{prf["lccs_placement"]})')
            if prf["black_border"]:
                amount = int(prf["black_border"]) if prf["lccs"].is_integer() else prf["black_border"]
                description += f'\n- {EmjMedals.bb} {amount} Black Border runs ' + \
                               placements_emojis.get(prf["lccs_placement"], f'(#{prf["lccs_placement"]})')

            embed.add_field(name=f"{format_data['emoji']} {format_data['name']} Stats", value=description, inline=True)

        if user.id == interaction.user.id and profile["avatarURL"] is None:
            embed.set_footer(
                text="You can set a profile picture either through the website "
                     "or the /oak command"
            )

        if not something:
            embed.description = f"-# Not much going on here...\n\n\n\n{EmjMisc.blank}"

        return MessageContent(embeds=[embed])

    @discord.app_commands.command(
        name="oak",
        description="Verify who you are in Bloons TD 6!",
    )
    @discord.app_commands.describe(
        str_oak="Your OAK (leave blank if you don't know what that is)",
    )
    @discord.app_commands.rename(str_oak="oak")
    async def cmd_verify(self, interaction: discord.Interaction, str_oak: str = None):
        instructions = "__**About verification**__\n" \
                       "To know who you are, I need your **Open Access Key (OAK)**. This is a bit of text that " \
                       "allows me to see your ingame profile picture and stats and things like that.\n\n" \
                       "__**Generate your OAK**__\n" \
                       "🔹 Open Bloons TD 6 (or any NK game) > Settings > My Account > Open Data API (it's a small " \
                       "link in the bottom right) > Generate Key. Your OAK should look something like " \
                       "`oak_h6ea...p1hr`.\n" \
                       "🔹 Copy it (note: the \"Copy\" button doesn't work, so just manually select it and do ctrl+C) " \
                       "and, do /oak and paste your OAK as a parameter.\n" \
                       "🔹 Congrats, you have verified yourself!\n\n" \
                       "__**More information**__\n" \
                       "Ninja Kiwi talking about OAKs: https://support.ninjakiwi.com/hc/en-us/articles/13438499873937\n"

        if str_oak is None:
            return await interaction.response.send_message(
                content=instructions,
                ephemeral=True,
            )

        if re.match(r"oak_[\da-z]+", str_oak) is None:
            return await interaction.response.send_message(
                content="Your OAK is not well formatted! it should be `oak_` followed by some numbers and/or lowercase "
                        "letters!\n\n"
                        "*Don't know what an OAK is? Leave the field blank to get a help message!*",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        if await get_btd6_user(str_oak) is None:
            return await interaction.edit_original_response(
                content="Couldn't find a BTD6 user with that OAK!\n"
                        "-# Are you sure it's the correct one?",
            )

        await set_oak(interaction.user, str_oak)
        await interaction.edit_original_response(
            content="✅ You OAK was set correctly! Your profile picture should appear in a bit!"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserCog(bot))
