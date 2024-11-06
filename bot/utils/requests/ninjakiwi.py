import io
import bot.utils.http

http = bot.utils.http


async def get_btd6_user(oak: str) -> dict | None:
    async with http.client.get(f"https://data.ninjakiwi.com/btd6/users/{oak}") as resp:
        if not resp.ok:
            return None
        data = await resp.json()
        if not data["success"]:
            return None
        return data["body"]


async def get_btd6_custom_map(code: str) -> dict | None:
    async with http.client.get(f"https://data.ninjakiwi.com/btd6/maps/map/{code}") as resp:
        if not resp.ok:
            return None
        data = await resp.json()
        if not data["success"]:
            return None
        return data["body"]
