import bot.utils.http
from config import API_BASE_URL
from bot.exceptions import MaplistResNotFound, ErrorStatusCode
from bot.types import Format


http = bot.utils.http


async def get_maplist_map(map_id: str) -> dict:
    async with http.client.get(f"{API_BASE_URL}/maps/{map_id.upper()}") as resp:
        if resp.status == 404:
            raise MaplistResNotFound("map")
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_maplist_config() -> dict:
    async with http.client.get(f"{API_BASE_URL}/config") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        config = await resp.json()
        return {cfg["name"]: cfg["value"] for cfg in config}


async def get_leaderboard(lb_type: str, game_format: Format, page: int) -> dict:
    fmt = {
        "Current Version": "current",
        "All Versions": "all",
    }.get(game_format, "current")
    value = {
        "Points": "points",
        "LCCs": "lccs",
    }.get(lb_type, "points")

    qstring = f"value={value}&version={fmt}&page={page}"
    async with http.client.get(f"{API_BASE_URL}/maps/leaderboard?{qstring}") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()
