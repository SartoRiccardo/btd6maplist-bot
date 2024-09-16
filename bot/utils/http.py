import asyncio
import os
import aiohttp_client_cache
import cryptography.hazmat.primitives.asymmetric.rsa
from config import DATA_PATH, PRIVKEY_PATH, PRIVKEY_PSWD
from cryptography.hazmat.primitives import serialization


client: aiohttp_client_cache.CachedSession | None = None
private_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey | None = None


async def init_http_client():
    cache = aiohttp_client_cache.SQLiteBackend(
        cache_name=os.path.join(DATA_PATH, ".cache", "aiohttp-requests.db"),
        expire_after=60*5,
        urls_expire_after={
            "data.ninjakiwi.com": 3600 * 24 * 7,
        },
        include_headers=True,
    )

    async def init_session():
        global client, private_key

        with open(PRIVKEY_PATH, "rb") as fin:
            private_key = serialization.load_pem_private_key(
                fin.read(),
                password=PRIVKEY_PSWD,
            )

        async with aiohttp_client_cache.CachedSession(cache=cache) as session:
            client = session
            while True:
                await session.delete_expired_responses()
                await asyncio.sleep(3600 * 24 * 5)

    asyncio.create_task(init_session())
