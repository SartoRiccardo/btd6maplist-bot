import hashlib
import hmac
import io
import os
import time

import aiohttp.hdrs
import discord
import bot.utils.http
from bot.exceptions import MaplistResNotFound, ErrorStatusCode, BadRequest
from bot.types import Format
from bot.utils.requests.maplist_types import (
    FullMap, MapEntry, RetroMap,
    CompletionEntry, CompletionMapBase, CompletionsPage, FormatData, MaplistConfig,
    LeaderboardPage, MaplistUser,
    LinkedRoleUpdate,
)
import json
from aiohttp import FormData
import urllib.parse

http = bot.utils.http
API_BASE_URL = os.environ["API_BASE_URL"]
BOT_SECRET = os.environ["BOT_SECRET"].encode()
os.makedirs(os.path.join(os.path.expanduser(os.environ.get("DATA_PATH", "~/data")), "tmp"), exist_ok=True)


def hmac_headers(method: str, path: str, body: bytes | str = "", content_type: str | None = "application/json") -> dict[str, str]:
    timestamp = str(int(time.time()))
    body_bytes = body if isinstance(body, bytes) else body.encode()
    message = f"{timestamp}\n{method.upper()}\n{path}\n".encode() + body_bytes
    signature = hmac.new(BOT_SECRET, message, hashlib.sha256).hexdigest()
    headers: dict[str, str] = {"X-Timestamp": timestamp, "X-Signature": signature}
    if content_type:
        headers["Content-Type"] = content_type
    return headers


class _BytesCapture:
    """Minimal async stream writer that captures bytes for HMAC signing."""
    def __init__(self) -> None:
        self._buf = bytearray()

    async def write(self, chunk: bytes) -> None:
        self._buf.extend(chunk)

    @property
    def data(self) -> bytes:
        return bytes(self._buf)



async def get_maplist_map(map_id: str) -> FullMap:
    async with http.client.get(f"{API_BASE_URL}/api/maps/{map_id.upper()}") as resp:
        if resp.status == 404:
            raise MaplistResNotFound("map")
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_experts() -> list[MapEntry]:
    async with http.client.get(f"{API_BASE_URL}/api/maps?format_id=51") as resp:
        return (await resp.json())["data"]


async def get_maplist() -> list[MapEntry]:
    async with http.client.get(f"{API_BASE_URL}/api/maps?format_id=1") as resp:
        return (await resp.json())["data"]


async def get_nostalgia_pack(game: int) -> list[MapEntry]:
    async with http.client.get(f"{API_BASE_URL}/api/maps?format_id=11&format_subfilter={game}") as resp:
        return (await resp.json())["data"]


async def get_botb(difficulty: int) -> list[MapEntry]:
    async with http.client.get(f"{API_BASE_URL}/api/maps?format_id=52&format_subfilter={difficulty}") as resp:
        return (await resp.json())["data"]


async def get_retro_maps() -> list[RetroMap]:
    async with http.client.get(f"{API_BASE_URL}/api/maps/retro") as resp:
        return (await resp.json())["data"]


async def get_completions(map_code: str, page: int, per_page: int | None = None) -> CompletionsPage:
    qparams = {"map_code": map_code, "page": page}
    if per_page is not None:
        qparams["per_page"] = per_page
    async with http.client.get(f"{API_BASE_URL}/api/completions?{urllib.parse.urlencode(qparams)}") as resp:
        return await resp.json()


async def get_map_lcc(map_code: str) -> CompletionEntry | None:
    qparams = {"map_code": map_code, "lcc": "only"}
    async with http.client.get(f"{API_BASE_URL}/api/completions?{urllib.parse.urlencode(qparams)}") as resp:
        data = (await resp.json())["data"]
        return next((c for c in data if c["is_current_lcc"]), None)


_VOTE_CHANNEL_ENV: dict[int, tuple[str, str]] = {
    1: ("MAPLIST_VOTE_CH_ID", "MAPLIST_VOTE_CH_ROLE_ID"),
    51: ("EXPLIST_VOTE_CH_ID", "EXPLIST_VOTE_CH_ROLE_ID"),
}


async def get_formats() -> list[FormatData]:
    async with http.client.get(f"{API_BASE_URL}/api/formats") as resp:
        formats = (await resp.json())["data"]
    for fmt in formats:
        env_keys = _VOTE_CHANNEL_ENV.get(fmt["id"])
        fmt["discord_vote_channel_id"] = os.environ.get(env_keys[0]) if env_keys else None
        fmt["discord_vote_channel_ping_role_id"] = os.environ.get(env_keys[1]) if env_keys else None
    return formats


async def get_maplist_config() -> MaplistConfig:
    async with http.client.get(f"{API_BASE_URL}/api/config") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_leaderboard(lb_type: str, game_format: Format, page: int, per_page: int | None = None) -> LeaderboardPage:
    fmt = {
        "Maplist": 1,
        # "Maplist ~ All Versions": 2,
        "Expert List": 51,
        "Nostalgia Pack": 11,
        "Best of the Best": 52,
    }.get(game_format, 1)
    value = {
        "Points": "points",
        "LCCs": "lccs",
        "No Optimal Hero": "no_geraldo",
        "Black Border": "black_border",
    }.get(lb_type, "points")

    qparams = {"value": value, "page": page, "per_page": per_page} if per_page else {"value": value, "page": page}
    async with http.client.get(f"{API_BASE_URL}/api/formats/{fmt}/leaderboard?{urllib.parse.urlencode(qparams)}") as resp:
        if resp.status == 404:
            raise MaplistResNotFound("leaderboard")
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_maplist_user(uid: int, include: list[str] | None = None) -> MaplistUser:
    if include is None:
        include = ["flair", "medals", "permissions", "ranks"]
    qparams = {"include": ",".join(include)}
    async with http.client.get(f"{API_BASE_URL}/api/users/{uid}?{urllib.parse.urlencode(qparams)}") as resp:
        if resp.status == 404:
            raise MaplistResNotFound("user")
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_user_completions(uid: int, page: int = 1, per_page: int | None = None) -> CompletionsPage:
    qparams = {"player_id": uid, "page": page}
    if per_page is not None:
        qparams["per_page"] = per_page
    async with http.client.get(f"{API_BASE_URL}/api/completions?{urllib.parse.urlencode(qparams)}") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def submit_map(
        user: discord.User,
        code: str,
        notes: str,
        proof: discord.Attachment,
        format_id: int,
        proposed_diff: int,
) -> None:
    path = "/bot/maps/submit"
    proof_contents = await proof.read()

    form_data = FormData()
    form_data.add_field("_user", json.dumps({"discord_id": str(user.id), "name": user.name}))
    form_data.add_field("code", code)
    form_data.add_field("format_id", str(format_id))
    form_data.add_field("proposed", str(proposed_diff))
    if notes:
        form_data.add_field("subm_notes", notes)
    form_data.add_field(
        "completion_proof",
        io.BytesIO(proof_contents),
        filename=proof.filename,
        content_type=proof.content_type,
    )

    writer = form_data()
    buf = _BytesCapture()
    await writer.write(buf)
    body = buf.data

    headers = hmac_headers("POST", path, body, content_type=None)
    headers["Content-Type"] = writer.content_type

    async with http.client.post(f"{API_BASE_URL}{path}", data=body, headers=headers) as resp:
        if resp.status == 422:
            raise BadRequest(await resp.json())
        if not resp.ok:
            raise ErrorStatusCode(resp.status)


async def submit_run(
        user: discord.User,
        map_id: str,
        proofs: list[discord.Attachment],
        no_optimal_hero: bool,
        black_border: bool,
        is_lcc: bool,
        notes: str | None,
        vproof_url: list[str],
        leftover: int | None,
        run_format: int,
) -> None:
    path = "/bot/completions/submit"

    form_data = FormData()
    form_data.add_field("_user", json.dumps({"discord_id": str(user.id), "name": user.name}))
    form_data.add_field("map", map_id)
    form_data.add_field("format_id", str(run_format))
    if black_border:
        form_data.add_field("black_border", "true")
    if no_optimal_hero:
        form_data.add_field("no_geraldo", "true")
    if is_lcc and leftover is not None:
        form_data.add_field("lcc", json.dumps({"leftover": leftover}))
    if notes:
        form_data.add_field("subm_notes", notes)
    for url in vproof_url:
        form_data.add_field("proof_videos", url)
    for file in proofs:
        fcontents = await file.read()
        form_data.add_field(
            "proof_images",
            io.BytesIO(fcontents),
            filename=file.filename,
            content_type=file.content_type,
        )

    writer = form_data()
    buf = _BytesCapture()
    await writer.write(buf)
    body = buf.data

    headers = hmac_headers("POST", path, body, content_type=None)
    headers["Content-Type"] = writer.content_type

    async with http.client.post(f"{API_BASE_URL}{path}", data=body, headers=headers) as resp:
        if resp.status == 400:
            raise BadRequest(await resp.json())
        if not resp.ok:
            raise ErrorStatusCode(resp.status)


async def read_rules(user: discord.User) -> None:
    path = "/bot/read-rules"
    body = json.dumps({"_user": {"discord_id": str(user.id), "name": user.name}})
    async with http.client.put(f"{API_BASE_URL}{path}", data=body, headers=hmac_headers("PUT", path, body)) as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)


async def set_oak(user: discord.User, oak: str | None = None) -> None:
    path = f"/bot/users/{user.id}"
    body = json.dumps({
        "_user": {"discord_id": str(user.id), "name": user.name},
        "nk_oak": oak,
    })
    async with http.client.put(f"{API_BASE_URL}{path}", data=body, headers=hmac_headers("PUT", path, body)) as resp:
        if resp.status == 422:
            raise BadRequest(await resp.json())
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)


async def accept_run(who: discord.User, message_id: int) -> None:
    path = "/bot/completions/accept"
    body = json.dumps({
        "_user": {"discord_id": str(who.id), "name": who.name},
        "completion_webhook_message_id": str(message_id),
    })
    async with http.client.post(f"{API_BASE_URL}{path}", data=body, headers=hmac_headers("POST", path, body)) as resp:
        if resp.status == 422:
            raise BadRequest(await resp.json())
        elif resp.status == 404:
            raise MaplistResNotFound("completion")
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)


async def reject_run(who: discord.User, message_id: int) -> None:
    path = "/bot/completions/reject"
    body = json.dumps({
        "_user": {"discord_id": str(who.id), "name": who.name},
        "completion_webhook_message_id": str(message_id),
    })
    async with http.client.post(f"{API_BASE_URL}{path}", data=body, headers=hmac_headers("POST", path, body)) as resp:
        if resp.status == 422:
            raise BadRequest(await resp.json())
        elif resp.status == 404:
            raise MaplistResNotFound("completion")
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)


def get_banner_medals_url(banner_url: str, medals: dict) -> str:
    banner_name = banner_url.split("/")[-1]
    return f"{os.environ['API_BASE_PUBLIC_URL']}/img/medal-banner/{banner_name}?{urllib.parse.urlencode(medals)}"


async def reject_map(who: discord.User, message_id: int) -> None:
    path = "/bot/maps/submit/reject"
    body = json.dumps({
        "_user": {"discord_id": str(who.id), "name": who.name},
        "webhook_message_id": str(message_id),
    })
    async with http.client.post(f"{API_BASE_URL}{path}", data=body, headers=hmac_headers("POST", path, body)) as resp:
        if resp.status == 422:
            raise BadRequest(await resp.json())
        elif resp.status == 404:
            raise MaplistResNotFound("map submission")
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)


async def search_maps(query: str) -> list[CompletionMapBase]:
    qparams = {"q": query, "entities": "maps"}
    async with http.client.get(f"{API_BASE_URL}/api/search?{urllib.parse.urlencode(qparams)}") as resp:
        if resp.ok:
            return [result["result"] for result in await resp.json()]
        return []


async def get_linked_role_updates() -> list[LinkedRoleUpdate]:
    path = "/bot/roles/achievement/updates"
    async with http.client.get(f"{API_BASE_URL}{path}", headers=hmac_headers("GET", path, "")) as resp:
        if not resp.ok:
            return []
        return await resp.json()


async def confirm_linked_role_updates() -> None:
    path = "/bot/roles/achievement/updates"
    async with http.client.post(f"{API_BASE_URL}{path}", headers=hmac_headers("POST", path, "")) as resp:
        pass
