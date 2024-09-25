import discord


class MessageContent:
    def __init__(
            self,
            *,
            content: str | None = None,
            embeds: list[discord.Embed] | None = None,
            view: discord.ui.View | None = None,
    ):
        self._content = content
        self._embeds = embeds
        self._view = view

    async def content(self) -> str | None:
        return self._content

    async def embeds(self) -> list[discord.Embed] | None:
        return self._embeds

    async def view(self) -> discord.ui.View | None:
        return self._view