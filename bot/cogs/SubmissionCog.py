import re
import discord
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.handlers import handle_error
from bot.utils.requests.maplist import submit_map, get_maplist_user, submit_run, get_maplist_map, accept_run, reject_run
from bot.views import VRulesAccept
from bot.views.modals import MapSubmissionModal, RunSubmissionModal
from bot.types import MapPlacement
from bot.exceptions import BadRequest, MaplistResNotFound
from config import MAPLIST_GID, WH_RUN_SUBMISSION_IDS, MAPLIST_ROLES, WEB_BASE_URL
from functools import wraps


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


async def check_submission(interaction: discord.Interaction, message: discord.Message) -> int | None:
    if message.webhook_id is None or \
            not len(message.embeds) or \
            message.embeds[0].footer.text is None or \
            (run_match := re.match(r"Run No\.(\d+)", message.embeds[0].footer.text)) is None:
        return await interaction.response.send_message(
            content="That's not a submission?",
            ephemeral=True,
        )
    run_id = int(run_match.group(1))

    subm_type = None
    for key in WH_RUN_SUBMISSION_IDS:
        if message.webhook_id in WH_RUN_SUBMISSION_IDS[key]:
            subm_type = key
            break

    if subm_type is None:
        return await interaction.response.send_message(
            content="That's not a submission?",
            ephemeral=True,
        )

    has_perms = False
    for rl in interaction.user.roles:
        if rl.id in (MAPLIST_ROLES["admin"] + MAPLIST_ROLES[f"{subm_type}_mod"]):
            has_perms = True
            break
    if not has_perms:
        return await interaction.response.send_message(
            content=f"You are not a {subm_type} mod",
            ephemeral=True,
        )

    return run_id


@discord.app_commands.context_menu(name="Accept Completion")
@discord.app_commands.guilds(MAPLIST_GID)
async def ctxm_accept_submission(interaction: discord.Interaction, message: discord.Message):
    run_id = await check_submission(interaction, message)
    if not isinstance(run_id, int):
        return

    await interaction.response.defer(ephemeral=True)
    try:
        await accept_run(interaction.user, run_id)
        response = "✅ Submitted successfully!\n" \
                   f"You can edit it [on the website]({WEB_BASE_URL}/completions/{run_id}) if needed."
    except BadRequest:
        response = "That run was already accepted!"
    except MaplistResNotFound:
        response = "Couldn't find that completion!\n" \
                   "-# Maybe it was rejected?"
    await interaction.edit_original_response(content=response)


@discord.app_commands.context_menu(name="Reject Completion")
@discord.app_commands.guilds(MAPLIST_GID)
async def ctxm_reject_submission(interaction: discord.Interaction, message: discord.Message):
    run_id = await check_submission(interaction, message)
    if not isinstance(run_id, int):
        return

    await interaction.response.defer(ephemeral=True)
    try:
        await reject_run(interaction.user, run_id)
        response = "✅ Deleted successfully!\n" \
                   f"If this was a mistake, you can insert it manually on the website, on the map's page."
    except BadRequest:
        response = "That run was already accepted!\n" \
                   "-# If you wanted to delete it, do so on the website."
    except MaplistResNotFound:
        response = "Couldn't find that completion!\n" \
                   "-# Maybe it was rejected?"
    await interaction.edit_original_response(content=response)


ctxm_accept_submission.error(handle_error)
ctxm_reject_submission.error(handle_error)


class SubmissionCog(CogBase):
    help_descriptions = {
        "submit": {
            "map": "Submit a map to either the Maplist or the Expert list!\n"
                   "-# If you wanna submit it to both, run the command twice.",
            "run": "Submit a completion to a maplist map. If required, you'll be asked for video proof "
                   "and your Round 100 saveup.",
            "lcc": "Shortcut for [[submit run]] with the `lcc` parameter set to `True`.",
        },
    }

    submit = SubmitGroup(
        name="submit",
        description="Submit something to the Maplist",
    )

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.bot.tree.add_command(ctxm_accept_submission)
        self.bot.tree.add_command(ctxm_reject_submission)

    async def cog_unload(self) -> None:
        await super().cog_load()
        self.bot.tree.remove_command(ctxm_accept_submission.name)
        self.bot.tree.remove_command(ctxm_reject_submission.name)

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
        if proof.size > 1024**2 * 3:
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

        modal = MapSubmissionModal(process_callback)

        # Note: this is an API call to the backend, it can only stay
        # within the 3-second Discord threshold because it's local, otherwise
        # it probably has to defer. But if it does, it can't show the modal.
        ml_user = await get_maplist_user(interaction.user.id, no_load_oak=True)
        if not ml_user["has_seen_popup"]:
            return await interaction.response.send_message(
                ephemeral=True,
                content=rules_msg,
                view=VRulesAccept(interaction, modal)
            )

        await interaction.response.send_modal(modal)

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
                "Experts / Medium-High",
                "Experts / High Expert",
                "Experts / High-True",
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
        if proof.size > 1024**2 * 3:
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

        modal = RunSubmissionModal(
            process_callback,
            is_lcc=lcc,
            req_video=lcc or no_optimal_hero or black_border,
        )

        try:
            ml_user = await get_maplist_user(interaction.user.id, no_load_oak=True)
        except MaplistResNotFound:
            ml_user = None

        if ml_user is None or not ml_user["has_seen_popup"]:
            return await interaction.response.send_message(
                ephemeral=True,
                content=rules_msg,
                view=VRulesAccept(interaction, modal)
            )

        await interaction.response.send_modal(modal)

    @staticmethod
    async def process_run_submission(
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
        await interaction.response.defer(thinking=True, ephemeral=True)

        map_id = map_id.upper()
        ml_map = await get_maplist_map(map_id)
        run_format = 1 if ml_map["difficulty"] == -1 else 51

        try:
            await submit_run(
                interaction.user,
                map_id,
                proof,
                no_optimal_hero,
                black_border,
                is_lcc,
                notes,
                vproof_url,
                leftover,
                run_format,
            )
            await interaction.edit_original_response(
                content="✅ Your completion was submitted!",
            )
        except BadRequest as exc:
            await interaction.edit_original_response(
                content=f"❌ Something went wrong: \n{exc.formatted_exc()}",
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubmissionCog(bot))
