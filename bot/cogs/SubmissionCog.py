import re
import discord
import asyncio
from discord.ext import commands
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.handlers import handle_error
from bot.utils.requests.maplist import (
    submit_map,
    get_maplist_user,
    submit_run,
    get_maplist_map,
    accept_run,
    reject_run,
    reject_map,
    search_maps,
    get_formats,
    get_retro_maps,
)
from bot.views import VRulesAccept, VRunFormatSelect
from bot.views.modals import MMapSubmission, MRunSubmission
from bot.exceptions import BadRequest, MaplistResNotFound
from config import WEB_BASE_URL
from bot.utils.misc import image_formats, max_upload_size_mb
from bot.utils.models import MessageContent
from collections.abc import Awaitable
from typing import Any
from difflib import SequenceMatcher

list_rules_url = "https://discord.com/channels/1162188507800944761/1162193272320569485/1272011602228678747"
exp_rules_url = "https://discord.com/channels/1162188507800944761/1250611476444479631/1253260417292308552"
rules_msg = "Before you submit anything, remember that there are RULES for " \
            "your run or map to be accepted **__You should read them!__** " \
            "They're a ~3 minute read.\n\n" \
            f"You can find them anytime at {list_rules_url} / {exp_rules_url}. **__If you " \
            f"submit something without reading them first, it might not be accepted!__**"


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
    return run_id


@discord.app_commands.context_menu(name="Accept Completion")
async def ctxm_accept_submission(interaction: discord.Interaction, message: discord.Message):
    run_id = await check_submission(interaction, message)
    if not isinstance(run_id, int):
        return

    await interaction.response.defer(ephemeral=True)
    try:
        await accept_run(interaction.user, run_id)
        response = "✅ Completion accepted!\n" \
                   f"You can edit it [on the website]({WEB_BASE_URL}/completions/{run_id}) if needed."
    except BadRequest:
        response = "That completion was already accepted!"
    except MaplistResNotFound:
        response = "Couldn't find that completion!\n" \
                   "-# Maybe it was rejected?"
    await interaction.edit_original_response(content=response)


ctxm_accept_submission.error(handle_error)


@discord.app_commands.context_menu(name="Reject Submission")
async def ctxm_reject_submission(interaction: discord.Interaction, message: discord.Message):
    async def reject_completion_submission():
        run_id = await check_submission(interaction, message)
        if not isinstance(run_id, int):
            return

        await interaction.response.defer(ephemeral=True)
        try:
            await reject_run(interaction.user, run_id)
            response = "✅ Rejected successfully!\n" \
                       f"If this was a mistake, you can insert it manually on the website, on the map's page."
        except BadRequest:
            response = "That run was already accepted!\n" \
                       "-# If you wanted to delete it, do so on the website."
        except MaplistResNotFound:
            response = "Couldn't find that completion!\n" \
                       "-# Maybe it was rejected?"
        await interaction.edit_original_response(content=response)

    async def reject_map_submission():
        if not len(message.embeds) or \
                message.embeds[0].title is None or \
                " - " not in message.embeds[0].title:
            return await interaction.response.send_message(
                content="That's not a submission?",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        try:
            await reject_map(interaction.user, message.id)
            response = "✅ Rejected successfully!\n" \
                       f"If this was a mistake, you can simply insert the map manually."
        except BadRequest:
            response = "That map was already accepted!\n" \
                       "-# If you wanted to delete it, do so on the website."
        except MaplistResNotFound:
            response = "Couldn't find that map!\n" \
                       "-# Maybe it was rejected?"
        await interaction.edit_original_response(content=response)

    if message.webhook_id:
        formats = await get_formats()
        for format_data in formats:
            if format_data["run_submission_wh"] and \
                    (match := re.match(r"https://discord.com/api/webhooks/(\d+)", format_data["run_submission_wh"])) and \
                    int(match.group(1)) == message.webhook_id:
                return await reject_completion_submission()
            if format_data["map_submission_wh"] and \
                    (match := re.match(r"https://discord.com/api/webhooks/(\d+)", format_data["map_submission_wh"])) and \
                    int(match.group(1)) == message.webhook_id:
                return await reject_map_submission()

    return await interaction.response.send_message(
        content="That's not a submission?",
        ephemeral=True,
    )


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

    @staticmethod
    async def check_submission_proof(interaction: discord.Interaction, proof: discord.Attachment) -> bool:
        if proof is None:
            return True

        if proof.size > 1024 ** 2 * max_upload_size_mb:
            await interaction.response.send_message(
                content=f"❌ Image size must be up to {max_upload_size_mb}MB",
                ephemeral=True,
            )
            return False
        if proof.content_type.split("/")[-1].lower() not in image_formats:
            await interaction.response.send_message(
                content=f"❌ Admissible image formats: `{'`, `'.join(image_formats)}`",
                ephemeral=True,
            )
            return False
        return True

    @submit.command(
        name="map",
        description="Submit a map to a list.",
    )
    @discord.app_commands.rename(
        map_code="code",
    )
    @discord.app_commands.describe(
        map_code="The BTD6 map's code",
        proof="Proof that you (or someone) beat CHIMPS on your map",
        submit_as="What would your map be?",
    )
    async def cmd_submit_map(
            self,
            interaction: discord.Interaction,
            map_code: str,
            submit_as: str,
            proof: discord.Attachment = None,
    ):
        check = await self.check_submission_proof(interaction, proof)
        if not check:
            return

        try:
            format_id, proposed = [int(x) for x in submit_as.split(";")]
        except ValueError:
            return await interaction.response.send_message(
                content="Couldn't decide what you were submitting your map as!\n"
                        "Try picking a value from the select options",
                ephemeral=True,
            )

        def process_callback(interaction: discord.Interaction, notes: str):
            return self.process_map_subm(
                interaction,
                map_code,
                proof,
                notes,
                format_id,
                proposed,
            )

        modal = MMapSubmission(process_callback)

        # Note: this is an API call to the backend, it can only stay
        # within the 3-second Discord threshold because it's local, otherwise
        # it probably has to defer. But if it does, it can't show the modal.
        try:
            ml_user = await get_maplist_user(interaction.user.id, no_load_oak=True)
        except MaplistResNotFound:
            ml_user = None

        if ml_user:
            permissions = set()
            for perms in ml_user["permissions"]:
                if perms["format"] is None or perms["format"] == format_id:
                    permissions.update(perms["permissions"])

            if "create:map_submission" not in permissions:
                return await interaction.response.send_message(
                    ephemeral=True,
                    content="You cannot submit maps to this list!",
                )

        if ml_user is None or not ml_user["has_seen_popup"]:
            return await interaction.response.send_message(
                ephemeral=True,
                content=rules_msg,
                view=VRulesAccept(interaction, modal)
            )

        formats = await get_formats()
        for fmt in formats:
            if fmt["id"] == format_id:
                if fmt["map_submission_status"] == "open_chimps" and proof is None:
                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="⚠️ Map submissions in this list require a screenshot of someone beating CHIMPS mode "
                                "in your map.\n\nSubmit the screenshot via the `proof` option when running this "
                                "command!",
                    )
                if fmt["map_submission_status"] == "closed":
                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="This list is not currently accepting map submissions.",
                    )

        await interaction.response.send_modal(modal)

    @staticmethod
    async def process_map_subm(
            interaction: discord.Interaction,
            map_code: str,
            proof: discord.Attachment,
            notes: str,
            format_id: int,
            proposed: int,
    ):
        await interaction.response.defer(
            ephemeral=True,
            thinking=True,
        )
        map_code = map_code.upper().strip()

        try:
            await submit_map(
                interaction.user,
                map_code,
                notes,
                proof,
                format_id,
                proposed,
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
        description="Submit a run on a map. If necessary, the command will ask you for video proof later!",
    )
    @discord.app_commands.rename(
        proof_opt_1="proof_optional_1",
        proof_opt_2="proof_optional_2",
        proof_opt_3="proof_optional_3",
    )
    @discord.app_commands.describe(
        proof=f"Image proof of you beating CHIMPS on the map (max {max_upload_size_mb}MB)",
        proof_opt_1="An additional proof image you may want to provide.",
        proof_opt_2="An additional proof image you may want to provide.",
        proof_opt_3="An additional proof image you may want to provide.",
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
            proof_opt_1: discord.Attachment = None,
            proof_opt_2: discord.Attachment = None,
            proof_opt_3: discord.Attachment = None,
    ):
        await self.submit_run(
            interaction,
            map_id,
            [proof, proof_opt_1, proof_opt_2, proof_opt_3],
            no_optimal_hero,
            black_border,
            is_lcc,
        )

    @submit.command(
        name="lcc",
        description="Submit a LCC on a map",
    )
    @discord.app_commands.describe(
        proof=f"Image proof of you beating CHIMPS on the map (max {max_upload_size_mb}MB)"
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
            [proof],
            no_optimal_hero,
            black_border,
            True,
        )

    @cmd_submit_run.autocomplete("map_id")
    @cmd_submit_lcc.autocomplete("map_id")
    async def autocomplete_map_id(self, _i: discord.Interaction, current: str) -> list[
        discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=map_data["name"], value=map_data["code"])
            for map_data in await search_maps(current)
        ]

    async def submit_run(
            self,
            interaction: discord.Interaction,
            map_id: str,
            proofs: list[discord.Attachment | None],
            no_optimal_hero: bool = False,
            black_border: bool = False,
            lcc: bool = False,
    ):
        proofs = [p for p in proofs if p is not None]
        for p in proofs:
            check = await self.check_submission_proof(interaction, p)
            if not check:
                return

        try:
            map_id = map_id.upper()
            ml_map = await get_maplist_map(map_id)
        except MaplistResNotFound:
            return await interaction.response.send_message(
                content="That map doesn't exist!",
                ephemeral=True,
            )

        format_keys = {
            1: "placement_curver",
            2: "placement_allver",
            11: "remake_of",
            51: "difficulty",
            52: "botb_difficulty",
        }

        formats = await get_formats()
        valid_formats = [
            format_data for format_data in formats
            if format_data["run_submission_status"] != "closed"
                and not format_data["hidden"]
                and ml_map[format_keys[format_data["id"]]] is not None
        ]

        if len(valid_formats) == 0:
            return await interaction.response.send_message(
                content="That map doesn't accept run submissions on any list it's on!",
                ephemeral=True,
            )

        async def process_callback(
                interaction: discord.Interaction,
                notes: str | None,
                vproof_url: list[str] | None,
                leftover: int | None,
                format_id: int = None,
        ) -> None:
            await self.process_run_submission(
                interaction,
                map_id,
                format_id,
                proofs,
                no_optimal_hero,
                black_border,
                lcc,
                notes,
                vproof_url if vproof_url else [],
                leftover,
            )

        def modal_builder(format_id: int) -> MRunSubmission:
            def callback_wrapper(*args) -> Awaitable[Any]:
                return process_callback(*args, format_id=format_id)

            permissions = set()
            if ml_user:
                for perms in ml_user["permissions"]:
                    if perms["format"] is None or perms["format"] == format_id:
                        permissions.update(perms["permissions"])

            return MRunSubmission(
                callback_wrapper,
                is_lcc=lcc,
                req_video=lcc or black_border or
                    no_optimal_hero and (
                        format_id == 1 or format_id == 2 or
                        format_id == 51 and not (0 <= ml_map["difficulty"] <= 2)
                    ) or
                    ml_user is not None and "require:completion_submission:recording" in permissions
            )

        try:
            ml_user = await get_maplist_user(interaction.user.id, no_load_oak=True)
        except MaplistResNotFound:
            ml_user = None

        if len(valid_formats) == 1:
            next_step = modal_builder(valid_formats[0]["id"])
        else:
            next_step = MessageContent(
                content="This map belongs to multiple lists, which may have different rules for their completions.\n\n"
                        "Please select which list you're submitting your run to.",
                view=VRunFormatSelect(interaction, valid_formats, modal_builder),
            )

        if ml_user is None or not ml_user["has_seen_popup"]:
            return await interaction.response.send_message(
                ephemeral=True,
                content=rules_msg,
                view=VRulesAccept(interaction, next_step)
            )

        if isinstance(next_step, discord.ui.Modal):
            await interaction.response.send_modal(next_step)
        elif isinstance(next_step, MessageContent):
            await interaction.response.send_message(
                ephemeral=True,
                content=await next_step.content(),
                embeds=await next_step.embeds(),
                view=await next_step.view(),
            )

    @staticmethod
    async def process_run_submission(
            interaction: discord.Interaction,
            map_id: str,
            run_format: int,
            proofs: list[discord.Attachment],
            no_optimal_hero: bool,
            black_border: bool,
            is_lcc: bool,
            notes: str | None,
            vproof_url: list[str],
            leftover: int | None,
    ):
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            await submit_run(
                interaction.user,
                map_id,
                proofs,
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

    @cmd_submit_map.autocomplete("submit_as")
    async def autoc_submit_map_submit_as(
            self,
            _interaction: discord.Interaction,
            current: str,
    ) -> list[discord.app_commands.Choice[str]]:
        retro_maps, formats = await asyncio.gather(
            get_retro_maps(),
            get_formats(),
        )

        choices = [
            (11, f"Nostalgia Pack / {map_data['name']}", map_data["id"])
            for map_data in retro_maps
        ]
        for format_data in formats:
            if format_data["proposed_difficulties"]:
                for i, choice_name in enumerate(format_data["proposed_difficulties"]):
                    choices.append((format_data["id"], f"{format_data['name']} ~ {choice_name}", i))

        choices = [(*c, SequenceMatcher(None, c[1], current).ratio()) for c in choices]
        return [
            discord.app_commands.Choice(name=name, value=f"{format_id};{value}")
            for format_id, name, value, score in sorted(choices, key=lambda x: x[-1], reverse=True)[:10]
        ]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SubmissionCog(bot))
