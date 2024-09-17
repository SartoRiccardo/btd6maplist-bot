import discord
from bot.types import SubmitMapModalCb
from .ModalBase import ModalBase


class MapSubmissionModal(ModalBase, title="Submit a Map"):
    notes = discord.ui.TextInput(
        label="Notes",
        placeholder="Additional notes about the map, if any (creators, verifiers, ...)",
        max_length=500,
        style=discord.TextStyle.paragraph,
        required=False,
    )

    def __init__(
            self,
            submit_cb: SubmitMapModalCb,
    ):
        super().__init__()
        self.submit_cb = submit_cb

    async def on_submit(self, interaction: discord.Interaction):
        notes = self.notes.value
        await self.submit_cb(interaction, notes if len(notes) else None)
