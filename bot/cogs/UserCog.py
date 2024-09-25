import asyncio
import math
import re
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.formulas import get_page_idxs
from bot.utils.requests.maplist import get_maplist_user, get_user_completions, set_oak
from bot.utils.requests.ninjakiwi import get_btd6_user
from bot.views import VPages, VPaginateList
from bot.utils.models import MessageContent
from bot.exceptions import MaplistResNotFound
from config import EMBED_CLR, WEB_BASE_URL
from bot.utils.emojis import EmjMedals, EmjIcons, EmjPlacements, EmjMisc


empty_profile = {
    "maplist": {
        "current": {"points": 0},
        "all": {"points": 0},
    },
    "created_maps": [],
    "avatarURL": "https://static-api.nkstatic.com/appdocs/4/assets/opendata/db32af61df5646951a18c60fe0013a31_ProfileAvatar01.png",
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

    async def send_user_profile(
            self,
            interaction: discord.Interaction,
            user: discord.User,
            hide: bool = False,
    ):
        await interaction.response.defer(ephemeral=hide)

        compl = None
        try:
            profile, compl = await asyncio.gather(
                get_maplist_user(user.id),
                get_user_completions(user.id),
            )
            comp_num = compl["total"]
        except MaplistResNotFound:
            comp_num = 0
            profile = empty_profile

        pages = [
            ("ℹ️", "User Overview", self.get_user_message(interaction, user, profile, comp_num)),
        ]
        if compl and comp_num > 0:
            pages.append((
                EmjMedals.win, "Completions",
                self.get_completions_message(interaction, user, compl,
                                             VPages(interaction, pages, placeholder="Other user info",
                                                    current_page=len(pages))),
            ))

        pages_view = None
        if len(pages) > 0:
            pages_view = VPages(interaction, pages, placeholder="Other user info")

        await interaction.edit_original_response(
            embeds=await pages[0][2].embeds(),
            view=pages_view,
        )

    @staticmethod
    def get_completions_message(
            interaction: discord.Interaction,
            user: discord.User,
            completions: dict,
            pages_view: VPages,
    ) -> MessageContent:
        items_page = 20
        items_page_srv = 50

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
                comp_medals = [EmjMedals.bb if entry["black_border"] else EmjMedals.win]
                if entry["format"] <= 50 and entry["no_geraldo"]:
                    comp_medals.append(EmjMedals.no_opt_hero)
                if entry["current_lcc"]:
                    comp_medals.append(EmjMedals.lcc)
                for _ in range(len(comp_medals), medal_spots):
                    comp_medals.insert(0, EmjMisc.blank)

                map_name = entry["map"]["name"]
                if i+1 < len(entries) and entry["map"]["code"] == entries[i+1]["map"]["code"]:
                    map_name = "↓     ↓     ↓     ↓"
                content += row_template.format(format_emj, " ".join(comp_medals), map_name)
            return content.strip()

        comp_pages = {1: completions}
        client_pages = math.ceil(completions["total"] / items_page)
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
            content=build_message(view.get_needed_rows(1, comp_pages)),
            view=view,
        )

    @staticmethod
    def get_user_message(
            interaction: discord.Interaction,
            user: discord.User,
            profile: dict,
            comp_num: int,
    ) -> MessageContent:
        description = ""
        if len(profile["created_maps"]):
            description += f"- **Created Maps:** {len(profile['created_maps'])}\n"
        if comp_num:
            description += f"- **Completions Submitted:** {EmjMedals.win} {comp_num}\n"
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
        embed.set_thumbnail(url=profile["avatarURL"] if profile["avatarURL"] else empty_profile["avatarURL"])
        if profile["maplist"]["current"]["points"]:  # Copy for allvers
            something = True
            prf = profile["maplist"]["current"]
            description = f'- {int(prf["points"]) if prf["points"].is_integer() else prf["points"]}pt ' + \
                          placements_emojis.get(prf["pts_placement"], f'(#{prf["pts_placement"]})')
            if prf["lccs"]:
                description += f'\n- {int(prf["lccs"]) if prf["lccs"].is_integer() else prf["lccs"]} LCCs ' + \
                               placements_emojis.get(prf["lccs_placement"], f'(#{prf["lccs_placement"]})')

            embed.add_field(
                name=f"{EmjIcons.curver} Maplist Stats",
                value=description,
                inline=True,
            )
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
