import asyncio
import os
import aiohttp_client_cache
from bot.utils.colors import purple


client: aiohttp_client_cache.CachedSession | None = None


async def init_http_client():
    cache = aiohttp_client_cache.SQLiteBackend(
        cache_name=os.path.join(os.path.expanduser(os.environ.get("DATA_PATH", "~/data")), ".cache", "aiohttp-requests.db"),
        expire_after=60*5,
        urls_expire_after={
            "data.ninjakiwi.com": 3600 * 24 * 7,
        },
        include_headers=True,
    )

    async def init_session():
        global client

        async with aiohttp_client_cache.CachedSession(cache=cache) as session:
            client = session
            print(f"{purple('[HTTP]')} Started session")
            while True:
                await session.delete_expired_responses()
                await asyncio.sleep(3600 * 24 * 5)

    asyncio.create_task(init_session())
