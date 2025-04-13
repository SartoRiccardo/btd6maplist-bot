import discord
from bot.types import SelectFormatCb


class FormatSelector(discord.ui.Select):
    def __init__(
            self,
            formats: list[dict],
            callback_func: SelectFormatCb,
    ):
        self.formats = formats
        self.callback_func = callback_func
        options = [
            discord.SelectOption(emoji=None, label=fmt["name"], value=str(fmt["id"]))
            for fmt in self.formats
        ]

        super().__init__(
            placeholder="Select the list...",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            format_data = next(fmt for fmt in self.formats if str(fmt["id"]) == self.values[0])
            await self.callback_func(interaction, format_data["id"])
        except StopIteration:
            pass
