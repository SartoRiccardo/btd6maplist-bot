import discord
from .components import OwnerButton


class VRulesAccept(discord.ui.View):
    """Paginates some information"""
    def __init__(
            self,
            interaction: discord.Interaction,
            modal: discord.ui.Modal,
            timeout: float = None,
    ):
        super().__init__(timeout=timeout)
        self.modal = modal

        self.add_item(OwnerButton(
            interaction.user,
            self.on_rules_read,
            style=discord.ButtonStyle.green,
            label="I have read the rules",
        ))

    async def on_rules_read(self, interaction: discord.Interaction):
        # API call to accept the rules (launch task)...
        await interaction.response.send_modal(self.modal)
