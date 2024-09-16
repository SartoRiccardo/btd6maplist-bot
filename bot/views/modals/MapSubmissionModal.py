import discord


class MapSubmissionModal(discord.ui.Modal, title="Submit a Map"):
    notes = discord.ui.TextInput(
        label="Notes",
        placeholder="Additional notes about the map, if any (creators, verifiers, ...)",
        style=discord.TextStyle.paragraph,
        required=False,
    )

    def __init__(
            self,
            submit_cb,
    ):
        super().__init__()
        self.submit_cb = submit_cb

    async def on_submit(self, interaction: discord.Interaction):
        await self.submit_cb(interaction, self.notes.value)
