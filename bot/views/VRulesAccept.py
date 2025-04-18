import asyncio
import discord
from bot.utils.requests.maplist import read_rules
from bot.utils.models.MessageContent import MessageContent


class VRulesAccept(discord.ui.View):
    """Prompts the user to accept the rules"""
    def __init__(
            self,
            interaction: discord.Interaction,
            next_step: discord.ui.Modal | MessageContent,
            timeout: float = None,
    ):
        super().__init__(timeout=timeout)
        self.next_step = next_step
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
        response_coro = interaction.response.send_modal(self.next_step) \
            if isinstance(self.next_step, discord.ui.Modal) else \
            interaction.response.edit_original_response(
                content=await self.next_step.content(),
                embeds=await self.next_step.embeds(),
                view=await self.next_step.view(),
            )

        await asyncio.gather(
            self.delete_og_interaction(),
            response_coro,
        )
