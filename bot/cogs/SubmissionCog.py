import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from config import MAPLIST_GID


@discord.app_commands.guilds(MAPLIST_GID)
class SubmitGroup(discord.app_commands.Group):
    pass


class SubmissionCog(CogBase):
    submit = SubmitGroup(
        name="submit",
        description="Submit something to the Maplist",

    )
    help_descriptions = {
        "verify": "Verify your BTD6 profile!",
    }

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @submit.command(
        name="map",
        description="Submit a map to the Maplist",
    )
    @discord.app_commands.rename(map_code="code")
    @discord.app_commands.describe(
        map_code="The BTD6 map's code",
        proof="Proof that you (or someone) beat CHIMPS on your map"
    )
    async def cmd_submit_map(
            self,
            interaction: discord.Interaction,
            map_code: str,
            proof: discord.Attachment,
    ):
        map_code = map_code.upper()
        await interaction.response.send_message(
            content="`501`",
            ephemeral=True,
        )

    @submit.command(
        name="run",
        description="Submit a run on a map",
    )
    @discord.app_commands.describe(
        proof="Image proof of you beating CHIMPS on the map (max 2MB)"
    )
    @autodoc
    async def cmd_submit_run(
            self,
            interaction: discord.Interaction,
            map_id: str,
            proof: discord.Attachment,
            no_optimal_hero: bool = False,
            black_border: bool = False,
            is_lcc: bool = False,
    ):
        await self.submit_run(
            interaction,
            map_id,
            proof,
            no_optimal_hero,
            black_border,
            is_lcc,
        )

    @submit.command(
        name="lcc",
        description="Submit a LCC on a map",
    )
    @discord.app_commands.describe(
        proof="Image proof of you beating CHIMPS on the map (max 2MB)"
    )
    @autodoc
    async def cmd_submit_lcc(
            self,
            interaction: discord.Interaction,
            map_id: str,
            proof: discord.Attachment,
            no_optimal_hero: bool = False,
            black_border: bool = False,
    ):
        await self.submit_run(
            interaction,
            map_id,
            proof,
            no_optimal_hero,
            black_border,
            True,
        )

    async def submit_run(
            self,
            interaction: discord.Interaction,
            map_id: str,
            proof: discord.Attachment,
            no_optimal_hero: bool = False,
            black_border: bool = False,
            lcc: bool = False,
    ):
        await interaction.response.send_message(
            content="`501`",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubmissionCog(bot))
