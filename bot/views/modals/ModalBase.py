from bot.utils.handlers import handle_error
import discord


class ModalBase(discord.ui.Modal):
    async def on_error(
            self,
            interaction: discord.Interaction,
            error: Exception,
    ) -> None:
        await handle_error(interaction, error)
