import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.requests.maplist import submit_map, get_maplist_user
from bot.views import VRulesAccept
from bot.views.modals import MapSubmissionModal, RunSubmissionModal
from bot.types import MapPlacement
from bot.exceptions import BadRequest
from config import MAPLIST_GID


list_rules_url = "https://discord.com/channels/1162188507800944761/1162193272320569485/1272011602228678747"
exp_rules_url = "https://discord.com/channels/1162188507800944761/1250611476444479631/1253260417292308552"
rules_msg = "Before you submit anything, remember that there are RULES for " \
            "your run or map to be accepted **__You should read them!__** " \
            "They're a ~3 minute read.\n\n" \
            f"You can find them anytime at {list_rules_url} / {exp_rules_url}. **__If you " \
            f"submit something without reading them first, it might not be accepted!__**"


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
    @discord.app_commands.rename(
        map_code="code",
        proposed="proposed_difficulty",
    )
    @discord.app_commands.describe(
        map_code="The BTD6 map's code",
        proof="Proof that you (or someone) beat CHIMPS on your map",
        proposed="What would your map be?",
    )
    async def cmd_submit_map(
            self,
            interaction: discord.Interaction,
            map_code: str,
            proposed: MapPlacement,
            proof: discord.Attachment,
    ):
        if proof.size > 2_000_000:
            return await interaction.response.send_message(
                content=f"❌ Image size must be up to 2MB",
                ephemeral=True,
            )
        if proof.content_type.split("/")[-1].lower() not in ["webp", "png", "jpeg", "jpg"]:
            return await interaction.response.send_message(
                content=f"❌ Admissible image formats: `webp`, `png`, `jpg`",
                ephemeral=True,
            )

        def process_callback(interaction: discord.Interaction, notes: str):
            return self.process_map_subm(
                interaction,
                map_code,
                proof,
                notes,
                proposed
            )

        # Note: this is an API call to the backend, it can only stay
        # within the 3-second Discord threshold because it's local, otherwise
        # it probably has to defer. But if it does, it can't show the modal.
        ml_user = await get_maplist_user(interaction.user.id, no_load_oak=True)
        if not ml_user["has_seen_popup"]:
            return await interaction.response.send_message(
                ephemeral=True,
                content=rules_msg,
                view=VRulesAccept(
                    interaction,
                    process_callback,
                )
            )

        await interaction.response.send_modal(
            MapSubmissionModal(process_callback)
        )

    @staticmethod
    async def process_map_subm(
            interaction: discord.Interaction,
            map_code: str,
            proof: discord.Attachment,
            notes: str,
            proposed: MapPlacement,
    ):
        proposed_idxs = {
            "list": [
                "Maplist / Top 3",
                "Maplist / Top 10",
                "Maplist / #11 ~ 20",
                "Maplist / #21 ~ 30",
                "Maplist / #31 ~ 40",
                "Maplist / #41 ~ 50",
            ],
            "experts": [
                "Experts / Casual Expert",
                "Experts / Casual-Medium",
                "Experts / Medium Expert",
                "Experts / Medium-Hard",
                "Experts / Hard Expert",
                "Experts / Hard-True",
                "Experts / True Expert",
            ],
        }

        await interaction.response.defer(
            ephemeral=True,
            thinking=True,
        )
        map_code = map_code.upper()
        mtype = "list" if proposed.split(" / ")[0] == "Maplist" else "experts"

        try:
            await submit_map(
                interaction.user,
                map_code,
                notes,
                proof,
                mtype,
                proposed_idxs[mtype].index(proposed),
            )
            await interaction.edit_original_response(
                content="✅ Your map was submitted!",
            )
        except BadRequest as exc:
            await interaction.edit_original_response(
                content=f"❌ Something went wrong: \n{exc.formatted_exc()}",
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
        if proof.size > 2_000_000:
            return await interaction.response.send_message(
                content=f"❌ Image size must be up to 2MB",
                ephemeral=True,
            )
        if proof.content_type.split("/")[-1].lower() not in ["webp", "png", "jpeg", "jpg"]:
            return await interaction.response.send_message(
                content=f"❌ Admissible image formats: `webp`, `png`, `jpg`",
                ephemeral=True,
            )

        async def process_callback(
                interaction: discord.Interaction,
                notes: str | None,
                vproof_url: str | None,
                leftover: int | None
        ):
            await self.process_run_submission(
                interaction,
                map_id,
                proof,
                no_optimal_hero,
                black_border,
                lcc,
                notes,
                vproof_url,
                leftover,
            )

        ml_user = await get_maplist_user(interaction.user.id, no_load_oak=True)
        if not ml_user["has_seen_popup"]:
            return await interaction.response.send_message(
                ephemeral=True,
                content=rules_msg,
                view=VRulesAccept(
                    interaction,
                    process_callback,
                )
            )

        await interaction.response.send_modal(
            RunSubmissionModal(
                process_callback,
                is_lcc=lcc,
                req_video=lcc or no_optimal_hero or black_border,
            )
        )

    async def process_run_submission(
            self,
            interaction: discord.Interaction,
            map_id: str,
            proof: discord.Attachment,
            no_optimal_hero: bool,
            black_border: bool,
            is_lcc: bool,
            notes: str | None,
            vproof_url: str | None,
            leftover: int | None,
    ):
        await interaction.response.send_message(
            content="`[501]` Not yet implemented!",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubmissionCog(bot))
