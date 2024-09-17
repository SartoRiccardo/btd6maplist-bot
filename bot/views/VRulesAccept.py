import asyncio
import discord
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

    async def delete_og_interaction(self):
        og_resp = await self.og_interaction.original_response()
        await og_resp.delete()

    async def interaction_check(self, _i: discord.Interaction, /) -> bool:
        return not self.read

    @discord.ui.button(
        label="I have read the rules",
        style=discord.ButtonStyle.green,
    )
    async def on_rules_read(self, interaction: discord.Interaction, _b: discord.ui.Button):
        self.read = True
        asyncio.create_task(read_rules(self.og_interaction.user))
        await asyncio.gather(
            self.delete_og_interaction(),
            interaction.response.send_modal(self.modal),
        )
