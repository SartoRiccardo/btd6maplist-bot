import asyncio
import discord
from .components import OwnerButton
from bot.utils.requests.maplist import read_rules


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
        self.og_interaction = interaction
        self.read = False

        self.add_item(OwnerButton(
            interaction.user,
            self.on_rules_read,
            style=discord.ButtonStyle.green,
            label="I have read the rules",
        ))

    async def delete_og_interaction(self):
        og_resp = await self.og_interaction.original_response()
        await og_resp.delete()

    async def interaction_check(self, _i: discord.Interaction, /) -> bool:
        return not self.read

    async def on_rules_read(self, interaction: discord.Interaction):
        self.read = True
        asyncio.create_task(read_rules(interaction.user.id))
        await asyncio.gather(
            self.delete_og_interaction(),
            interaction.response.send_modal(self.modal),
        )
