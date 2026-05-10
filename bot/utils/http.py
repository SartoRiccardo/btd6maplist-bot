import asyncio
import os
import aiohttp_client_cache
import cryptography.hazmat.primitives.asymmetric.rsa
from cryptography.hazmat.primitives import serialization
from bot.utils.colors import purple


client: aiohttp_client_cache.CachedSession | None = None
private_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey | None = None


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
        global client, private_key

        with open(os.environ.get("PRIVKEY_PATH", "btd6maplist-bot.pem"), "rb") as fin:
            _privkey_pswd = os.environ.get("PRIVKEY_PSWD", "")
            private_key = serialization.load_pem_private_key(
                fin.read(),
                password=_privkey_pswd.encode() if _privkey_pswd else None,
            )
            print(f"{purple('[HTTP]')} Loaded private key")

        async with aiohttp_client_cache.CachedSession(cache=cache) as session:
            client = session
            print(f"{purple('[HTTP]')} Started session")
            while True:
                await session.delete_expired_responses()
                await asyncio.sleep(3600 * 24 * 5)

    asyncio.create_task(init_session())
