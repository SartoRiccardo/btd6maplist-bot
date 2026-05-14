import os


def get_embed_color() -> int:
    return int(os.environ["EMBED_CLR"], 16)


def get_co_owner_ids() -> list[int]:
    return [int(x) for x in os.environ.get("CO_OWNER_IDS", "").split(",") if x.strip()]


def get_nk_preview_proxy(code: str) -> str:
    return os.environ["NK_PREVIEW_PROXY_URL"].format(code=code)
