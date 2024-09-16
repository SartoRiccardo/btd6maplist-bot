import asyncio
import discord


class VTryAgain(discord.ui.View):
    """Opens a modal again after an error message."""
    def __init__(
            self,
            interaction: discord.Interaction,
            modal: discord.ui.Modal,
            timeout: float = None,
    ):
        super().__init__(timeout=timeout)
        self.og_interaction = interaction
        self.modal = modal
        self.opened = False

    async def delete_og_interaction(self):
        og_resp = await self.og_interaction.original_response()
        await og_resp.delete()

    @discord.ui.button(
        label="Try again",
        style=discord.ButtonStyle.danger,
    )
    async def reopen_modal(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        if self.opened:
            return await interaction.response.send_message(
                content="You can only reopen the modal once. Try running the command again!",
                ephemeral=True,
            )

        self.opened = True
        await asyncio.gather(
            self.delete_og_interaction(),
            interaction.response.send_modal(self.modal),
        )
