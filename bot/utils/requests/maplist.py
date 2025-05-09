import io
import os

import aiohttp.hdrs
import discord
import bot.utils.http
from config import API_BASE_URL, API_BASE_PUBLIC_URL, DATA_PATH
from bot.exceptions import MaplistResNotFound, ErrorStatusCode, BadRequest
from bot.types import Format
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, utils
import json
from aiohttp import FormData
import base64
import urllib.parse

http = bot.utils.http
os.makedirs(os.path.join(DATA_PATH, "tmp"), exist_ok=True)


# Signature methods & vulnerabilities: https://en.wikipedia.org/wiki/Digital_signature#Method
# Good article on RSA signatures: https://cryptobook.nakov.com/digital-signatures/rsa-signatures
def sign(message: bytes) -> str:
    # https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#signing
    signature = http.private_key.sign(
        message,
        padding=padding.PSS(
            padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        algorithm=hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


def partial_sign(message: bytes, current: hashes.Hash | None = None) -> hashes.Hash:
    if current is None:
        current = hashes.Hash(hashes.SHA256())
    current.update(message)
    return current


def finish_sign(current: hashes.Hash) -> str:
    sha256 = hashes.SHA256()

    digest = current.finalize()
    signature = http.private_key.sign(
        digest,
        padding.PSS(
            padding.MGF1(sha256),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        utils.Prehashed(sha256),
    )
    return base64.b64encode(signature).decode()


async def get_maplist_map(map_id: str) -> dict:
    async with http.client.get(f"{API_BASE_URL}/maps/{map_id.upper()}") as resp:
        if resp.status == 404:
            raise MaplistResNotFound("map")
        elif not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_experts() -> list:
    async with http.client.get(f"{API_BASE_URL}/maps?format=51") as resp:
        return await resp.json()


async def get_maplist() -> list:
    async with http.client.get(f"{API_BASE_URL}/maps?format=1") as resp:
        return await resp.json()


async def get_nostalgia_pack(game: int) -> list:
    async with http.client.get(f"{API_BASE_URL}/maps?format=11&filter={game}") as resp:
        return await resp.json()


async def get_botb(difficulty: int) -> list:
    async with http.client.get(f"{API_BASE_URL}/maps?format=52&filter={difficulty}") as resp:
        return await resp.json()


async def get_retro_maps(as_list: bool = True) -> list:
    async with http.client.get(f"{API_BASE_URL}/maps/retro") as resp:
        maps = await resp.json()
        if not as_list:
            return maps
        return [
            {**map_data, "game": game}
            for game in maps
            for category in maps[game]
            for map_data in maps[game][category]
        ]


async def get_map_completions(map_code: str, page: int) -> list:
    qparams = {page: page}
    async with http.client.get(f"{API_BASE_URL}/maps/{map_code}/completions?{urllib.parse.urlencode(qparams)}") as resp:
        return await resp.json()


async def get_formats() -> list[dict]:
    qparams = {"signature": sign(b"")}
    async with http.client.get(f"{API_BASE_URL}/formats/bot?{urllib.parse.urlencode(qparams)}") as resp:
        return await resp.json()


async def get_maplist_config() -> dict:
    async with http.client.get(f"{API_BASE_URL}/config") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_leaderboard(lb_type: str, game_format: Format, page: int) -> dict:
    fmt = {
        "Maplist": "1",
        # "Maplist ~ All Versions": "2",
        "Expert List": "51",
    }.get(game_format, "current")
    value = {
        "Points": "points",
        "LCCs": "lccs",
        "No Optimal Hero": "no_geraldo",
        "Black Border": "black_border",
    }.get(lb_type, "points")

    qstring = f"value={value}&format={fmt}&page={page}"
    async with http.client.get(f"{API_BASE_URL}/maps/leaderboard?{qstring}") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_maplist_user(uid: int, no_load_oak: bool = False) -> dict:
    message = f"{uid}{no_load_oak}"
    signature = sign(message.encode())
    qparams = {"signature": signature, "no_load_oak": str(no_load_oak)}
    url = f"{API_BASE_URL}/users/{uid}/bot?{urllib.parse.urlencode(qparams)}"
    async with http.client.get(url) as resp:
        if resp.status == 404:
            raise MaplistResNotFound("user")
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def get_user_completions(uid: int, page: int = 1) -> dict:
    qparams = {page: page}
    async with http.client.get(f"{API_BASE_URL}/users/{uid}/completions?{urllib.parse.urlencode(qparams)}") as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)
        return await resp.json()


async def submit_map(
        user: discord.User,
        code: str,
        notes: str,
        proof: discord.Attachment | None,
        map_type: int,
        proposed_diff: int,
) -> None:
    data = {
        "user": {
            "id": user.id,
            "username": user.name,
            "avatar_url": user.avatar.url,
        },
        "code": code,
        "notes": notes,
        "format": map_type,
        "proposed": proposed_diff,
    }

    form_data = None
    json_data = None
    if proof is None:
        json_data = {
            "data": json.dumps(data),
            "signature": sign(json.dumps(data).encode())
        }
    else:
        data_str = json.dumps(data)
        proof_contents = await proof.read()
        signature = sign(data_str.encode() + proof_contents)

        form_data = FormData()
        form_data.add_field(
            "proof_completion",
            io.BytesIO(proof_contents),
            filename=proof.filename,
            content_type=proof.content_type,
        )
        form_data.add_field("data", json.dumps({"data": data_str, "signature": signature}))

    async with http.client.post(f"{API_BASE_URL}/maps/submit/bot", data=form_data, json=json_data) as resp:
        if resp.status == 400:
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
    data = {
        "user": {
            "id": user.id,
            "username": user.name,
            "avatar_url": user.display_avatar.url,
        },
        "format": run_format,
        "notes": notes,
        "black_border": black_border,
        "no_geraldo": no_optimal_hero,
        "current_lcc": is_lcc,
        "leftover": leftover,
        "video_proof_url": vproof_url,
    }
    data_str = json.dumps(data)
    contents_hash = partial_sign((map_id+data_str).encode())

    form_data = FormData()
    for i, file in enumerate(proofs):
        fcontents = await file.read()
        contents_hash = partial_sign(fcontents, current=contents_hash)
        form_data.add_field(
            f"proof_completion[{i}]",
            io.BytesIO(fcontents),
            filename=file.filename,
            content_type=file.content_type,
        )
    form_data.add_field("data", json.dumps({"data": data_str, "signature": finish_sign(contents_hash)}))

    async with http.client.post(f"{API_BASE_URL}/maps/{map_id}/completions/submit/bot", data=form_data) as resp:
        if resp.status == 400:
            raise BadRequest(await resp.json())
        if not resp.ok:
            raise ErrorStatusCode(resp.status)


async def read_rules(user: discord.User) -> None:
    data = {
        "user": {
            "id": str(user.id),
            "username": user.name,
            "name": user.display_name,
        },
    }
    data_str = json.dumps(data)
    signature = sign(data_str.encode())

    payload = {"data": data_str, "signature": signature}
    async with http.client.put(f"{API_BASE_URL}/read-rules/bot", json=payload) as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)


async def set_oak(user: discord.User, oak: str) -> None:
    data = {
        "user": {
            "id": str(user.id),
            "username": user.name,
            "name": user.display_name,
        },
        "oak": oak,
    }
    data_str = json.dumps(data)
    signature = sign(f"{user.id}{data_str}".encode())

    payload = {"data": data_str, "signature": signature}
    async with http.client.put(f"{API_BASE_URL}/users/{user.id}/bot", json=payload) as resp:
        if not resp.ok:
            raise ErrorStatusCode(resp.status)


async def accept_run(who: discord.User, run_id: int) -> None:
    data = {
        "user": {
            "id": str(who.id),
            "username": who.name,
            "name": who.display_name,
        },
    }
    data_str = json.dumps(data)
    signature = sign(f"{run_id}{data_str}".encode())

    payload = {"data": data_str, "signature": signature}
    async with http.client.put(f"{API_BASE_URL}/completions/{run_id}/accept/bot", json=payload) as resp:
        if resp.status == 400:
            raise BadRequest(await resp.json())
        elif resp.status == 404:
            raise MaplistResNotFound("completion")
        if not resp.ok:
            errors = None
            if "application/json" in resp.headers.get(aiohttp.hdrs.CONTENT_TYPE) and \
                    "errors" in (resp_data := await resp.json()):
                errors = resp_data["errors"]
            raise ErrorStatusCode(resp.status, errors=errors)


async def reject_run(who: discord.User, run_id: int) -> None:
    data = {
        "user": {
            "id": str(who.id),
            "username": who.name,
            "name": who.display_name,
        },
    }
    data_str = json.dumps(data)
    signature = sign(f"{run_id}{data_str}".encode())

    payload = {"data": data_str, "signature": signature}
    async with http.client.delete(f"{API_BASE_URL}/completions/{run_id}/bot", json=payload) as resp:
        if resp.status == 400:
            raise BadRequest(await resp.json())
        elif resp.status == 404:
            raise MaplistResNotFound("completion")
        if not resp.ok:
            errors = None
            if "application/json" in resp.headers.get(aiohttp.hdrs.CONTENT_TYPE) and \
                    "errors" in (resp_data := await resp.json()):
                errors = resp_data["errors"]
            raise ErrorStatusCode(resp.status, errors=errors)


def get_banner_medals_url(banner_url: str, medals: dict) -> str:
    banner_name = banner_url.split("/")[-1]
    return f"{API_BASE_PUBLIC_URL}/img/medal-banner/{banner_name}?{urllib.parse.urlencode(medals)}"


async def reject_map(who: discord.User, message_id: int) -> None:
    data = {
        "user": {
            "id": str(who.id),
            "username": who.name,
            "name": who.display_name,
        },
        "message_id": str(message_id),
    }
    data_str = json.dumps(data)
    signature = sign(data_str.encode())

    payload = {"data": data_str, "signature": signature}
    async with http.client.delete(f"{API_BASE_URL}/maps/submit/bot", json=payload) as resp:
        if resp.status == 400:
            raise BadRequest(await resp.json())
        elif resp.status == 404:
            raise MaplistResNotFound("map submission")
        if not resp.ok:
            errors = None
            if "application/json" in resp.headers.get(aiohttp.hdrs.CONTENT_TYPE) and \
                    "errors" in (resp_data := await resp.json()):
                errors = resp_data["errors"]
            raise ErrorStatusCode(resp.status, errors=errors)


async def search_maps(query: str) -> list[dict]:
    qparams = {"q": query, "type": "map"}
    async with http.client.get(f"{API_BASE_URL}/search?{urllib.parse.urlencode(qparams)}") as resp:
        if resp.ok:
            return [result["data"] for result in await resp.json()]
        return []


async def get_linked_role_updates() -> list[dict]:
    qparams = {"signature": sign(b"")}
    async with http.client.get(f"{API_BASE_URL}/roles/achievement/updates/bot?{urllib.parse.urlencode(qparams)}") as resp:
        if not resp.ok:
            return []
        return await resp.json()


async def confirm_linked_role_updates() -> None:
    qparams = {"signature": sign(b"")}
    async with http.client.post(f"{API_BASE_URL}/roles/achievement/updates/bot?{urllib.parse.urlencode(qparams)}") as resp:
        pass
