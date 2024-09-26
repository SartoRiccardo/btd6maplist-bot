TOKEN = "bot-token-here"
APP_ID = "app-id-here"
PRIVKEY_PATH = "btd6maplist-bot.pem"
PRIVKEY_PSWD = None

API_BASE_PUBLIC_URL = "http://localhost:4000"
API_BASE_URL = "http://localhost:4000"  # You can reference the Docker container if you do that
WEB_BASE_URL = "http://localhost:3000"
# Discord doesn't embed URLs with a file extension, and NK's map preview urls don't have one. Proxy it somehow.
NK_PREVIEW_PROXY = lambda code: f"http://localhost:5000/map/{code}.jpg"

DATA_PATH = "data"  # Path to store non-volatile data such as cog states

BOT_NAME = "Boilerplate bot"
GH_REPO = "https://github.com/SartoRiccardo/discord-bot-boilerplate"
EMBED_CLR = 0xffd54f
MAPLIST_GID = 1162188507800944761
MAPLIST_ROLES: dict[str, list[int]] = {
    "admin": [],
    "expert_mod": [],
    "list_mod": [],
    "banned": [],
}
WH_RUN_SUBMISSION_IDS: dict[str, list[int]] = {
    "expert": [],
    "list": [],
}

# Will have access to the commands in bot/cogs/OwnerCog.py
CO_OWNER_IDS: list[int] = [

]