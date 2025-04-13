import discord

from .MessageContent import MessageContent
from typing import Awaitable, Callable


class LazyMessageContent(MessageContent):
    def __init__(self, request_cb: Callable[[], Awaitable[MessageContent]]):
        super().__init__()
        self.request_cb = request_cb
        self._loaded = False

    async def _load(self):
        self._loaded = True
        data = await self.request_cb()
        self._content = await data.content()
        self._embeds = await data.embeds()
        self._view = await data.view()

    async def content(self) -> str | None:
        if not self._loaded:
            await self._load()
        return self._content

    async def embeds(self) -> list[discord.Embed]:
        if not self._loaded:
            await self._load()
        return self._embeds if self._embeds else []

    async def view(self) -> str | None:
        if not self._loaded:
            await self._load()
        return self._view
