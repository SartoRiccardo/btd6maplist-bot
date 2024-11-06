import re
import discord
import validators
from bot.types import SubmitRunModalCb
import bot.views
from bot.utils.emojis import EmjMisc
from .ModalBase import ModalBase


class MRunSubmission(ModalBase, title="Submit a Completion"):
    def __init__(
            self,
            submit_cb: SubmitRunModalCb,
            is_lcc: bool = False,
            req_video: bool = False,
            init_values: dict = None,
    ):
        super().__init__()
        self.submit_cb = submit_cb
        self.is_lcc = is_lcc
        self.req_video = req_video

        init_values = init_values if init_values is not None else {}

        self.notes = discord.ui.TextInput(
            label="Notes",
            placeholder="Additional notes about the run, if any (people who helped, "
                        "strategy, ...)",
            max_length=500,
            style=discord.TextStyle.paragraph,
            required=False,
            default=init_values.get("notes", None),
        )
        self.add_item(self.notes)

        self.vproof_url = None
        if self.req_video or self.is_lcc:
            self.vproof_url = discord.ui.TextInput(
                label="Video Proof URL(s)",
                placeholder="https://youtube.com/... https://youtube.com/... ",
                required=True,
                default=init_values.get("vproof_url", None),
            )
            self.add_item(self.vproof_url)

        self.lcc_saveup = None
        if self.is_lcc:
            self.lcc_saveup = discord.ui.TextInput(
                label="LCC Saveup",
                placeholder="How much money you had left",
                required=True,
                default=init_values.get("lcc_saveup", None),
            )
            self.add_item(self.lcc_saveup)

    def validate_fields(self) -> str | None:
        if self.vproof_url and len(self.get_vproof_urls()) == 0:
            return "Proof URL doesn't have valid links!"
        if self.lcc_saveup and not self.lcc_saveup.value.isnumeric():
            return "LCC Saveup must be a positive number!"

    def get_vproof_urls(self) -> list[str] | None:
        if self.vproof_url is None:
            return None
        words = re.split(r"\s+", self.vproof_url.value)
        return [wd for wd in words if validators.url(wd)]

    async def on_submit(self, interaction: discord.Interaction):
        if err := self.validate_fields():
            try_again_view = bot.views.VTryAgain(
                interaction,
                MRunSubmission(
                    self.submit_cb, self.is_lcc, self.req_video,
                    init_values={
                        "notes": self.notes.value,
                        "vproof_url": self.vproof_url.value if self.vproof_url else None,
                        "lcc_saveup": self.lcc_saveup.value if self.lcc_saveup else None,
                    },
                )
            )

            return await interaction.response.send_message(
                content=f"❌  {err}\n{EmjMisc.blank}",
                ephemeral=True,
                view=try_again_view,
            )

        notes = self.notes.value
        saveup = int(self.lcc_saveup.value) if self.lcc_saveup else None

        await self.submit_cb(
            interaction,
            notes if len(notes) else None,
            self.get_vproof_urls(),
            saveup,
        )
