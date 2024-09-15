import asyncio
import re
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.requests.maplist import get_maplist_user, get_user_completions
from bot.exceptions import MaplistResNotFound
from config import EMBED_CLR, MAPLIST_INVITE
from bot.utils.emojis import EmjMedals, EmjIcons, EmjPlacements


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
        "verify": "Verify your BTD6 profile!",
    }

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @discord.app_commands.command(
        name="user",
        description="Check an user's Maplist stats",
    )
    @discord.app_commands.describe(user="The user to check")
    @autodoc
    async def cmd_user(
            self,
            interaction: discord.Interaction,
            user: discord.User,
            hide: bool = False,
    ):
        if user == self.bot.user:
            return await interaction.response.send_message(
                content="That's me!",
                ephemeral=True,
            )
        await self.send_user_profile(interaction, user, hide)

    @discord.app_commands.command(
        name="profile",
        description="Check your own profile!",
    )
    @autodoc
    async def cmd_profile(
            self,
            interaction: discord.Interaction,
            hide: bool = False,
    ):
        await self.send_user_profile(interaction, interaction.user, hide)

    async def send_user_profile(
            self,
            interaction: discord.Interaction,
            user: discord.User,
            hide: bool = False,
    ):
        await interaction.response.defer(ephemeral=hide)

        try:
            profile, compl = await asyncio.gather(
                get_maplist_user(user.id),
                get_user_completions(user.id),
            )
            comp_num = compl["total"]
        except MaplistResNotFound:
            comp_num = 0
            profile = empty_profile

        description = ""
        if len(profile["created_maps"]):
            description += f"- **Created Maps:** {len(profile['created_maps'])}\n"
        if comp_num:
            description += f"- **Completions Submitted:** {EmjMedals.win} {comp_num}\n"

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
                description += f'\n- {int(prf["lccs"]) if prf["lccs"].is_integer() else prf["lccs"]}pt ' + \
                               placements_emojis.get(prf["lccs_placement"], f'(#{prf["lccs_placement"]})')

            embed.add_field(
                name=f"{EmjIcons.curver} Maplist Stats",
                value=description,
                inline=True,
            )
        if user.id == interaction.user.id:
            embed.set_footer(
                text="You can set a profile picture either through the website "
                     "or the /verify command"
            )

        if not something:
            embed.description = "-# Not much going on here..."

        await interaction.edit_original_response(
            embed=embed,
        )

    @discord.app_commands.command(
        name="verify",
        description="Verify who you are in Bloons TD 6!",
    )
    @discord.app_commands.describe(
        str_oak="Your OAK (leave blank if you don't know what that is)",
    )
    @discord.app_commands.rename(str_oak="oak")
    async def cmd_verify(self, interaction: discord.Interaction, str_oak: str = None):
        instructions = "__**About verification**__\n" \
                       "To know who you are, I need your **Open Access Key (OAK)**. This is a bit of text that " \
                       "allows me to see a lot of things about you in-game, like your profile, your team, and " \
                       "more. It's perfectly safe though, Ninja Kiwi takes privacy very seriously, so I can't do " \
                       "anything bad with it even if I wanted to!\n\n" \
                       "__**Generate your OAK**__\n" \
                       "🔹 Open Bloons TD 6 (or Battles 2) > Settings > My Account > Open Data API (it's a small " \
                       "link in the bottom right) > Generate Key. Your OAK should look something like " \
                       "`oak_h6ea...p1hr`.\n" \
                       "🔹 Copy it (note: the \"Copy\" button doesn't work, so just manually select it and do ctrl+C) " \
                       "and, do /verify and paste your OAK as a parameter. Congrats, you have verified yourself!\n\n" \
                       "__**What if I have alts?**__\n" \
                       "You can register multiple accounts! One of them will be your \"main one\" which will be used " \
                       "as the default for all commands (you can choose which one via the /verify main command).\n\n" \
                       "__**More information**__\n" \
                       "Ninja Kiwi talking about OAKs: https://support.ninjakiwi.com/hc/en-us/articles/13438499873937\n"

        if str_oak is None:
            return await interaction.response.send_message(
                content=instructions,
                ephemeral=True,
            )

        if re.match(r"oak_[\da-z]{32}", str_oak) is None:
            return await interaction.edit_original_response(
                content="Your OAK is not well formatted! it should be `oak_` followed by 32 numbers and/or lowercase "
                        "letters!\n\n"
                        "*Don't know what an OAK is? Leave the field blank to get a help message!*",
            )

        await interaction.response.defer(ephemeral=True)
        # try:
        #     # Make a call to the Maplist API
        #     pass
        # except bloonspy.exceptions.NotFound:
        #     await interaction.edit_original_response(
        #         content="Couldn't find a BTD6 user with that OAK!\n"
        #                 "-# Are you sure it's the correct one?",
        #     )
        await interaction.response.edit_original_response(content="`501`")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserCog(bot))