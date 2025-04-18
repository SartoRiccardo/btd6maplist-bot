import discord
import asyncio
from bot.types import BuildRunModalCb
from .components.FormatSelector import FormatSelector


class VRunFormatSelect(discord.ui.View):
    def __init__(
            self,
            og_interaction: discord.Interaction,
            format_ids: list[dict],
            build_modal_cb: BuildRunModalCb,
            timeout: float = None,
    ):
        super().__init__(timeout=timeout)
        self.og_interaction = og_interaction
        self.format_ids = format_ids
        self.build_modal_cb = build_modal_cb

        self.add_item(FormatSelector(
            self.format_ids,
            self.on_format_select,
        ))

    async def delete_og_interaction(self) -> None:
        og_resp = await self.og_interaction.original_response()
        await og_resp.delete()

    async def on_format_select(
            self,
            interaction: discord.Interaction,
            format_id: int,
    ) -> None:
        modal = self.build_modal_cb(format_id)
        await asyncio.gather(
            self.delete_og_interaction(),
            interaction.response.send_modal(modal),
        )
