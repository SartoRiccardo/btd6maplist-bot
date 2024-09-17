import os
import discord
import logging
from datetime import datetime
from pathlib import Path
import bot.utils.http
from bot import __version__
from discord.ext import commands
from config import TOKEN, APP_ID, DATA_PATH
from bot.utils.colors import purple


class MaplistBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # intents.message_content = True
        # intents.members = True
        super().__init__(
            command_prefix=commands.when_mentioned_or(",,,"),
            intents=intents,
            application_id=APP_ID,
            activity=discord.Game(name=f"/help"),
        )
        self.remove_command("help")
        self.version = __version__
        self.last_restart = datetime.now()
        self.synced_tree = None
        if not os.path.exists("tmp"):
            os.mkdir("tmp")

    async def setup_hook(self):
        cogs = [
            "OwnerCog",
            "UtilsCog",
            "MapInfoCog",
            "LeaderboardCog",
            "UserCog",
            "SubmissionCog",
        ]
        for cog in cogs:
            await self.load_extension(f"bot.cogs.{cog}")

        await bot.utils.http.init_http_client()
        print(f"{purple('[BTD6Maplist Bot]')} Started!")

    async def get_app_command(self, cmd_name: str) -> discord.app_commands.AppCommand or None:
        if self.synced_tree is None:
            self.synced_tree = await self.tree.fetch_commands()
        return discord.utils.get(self.synced_tree, name=cmd_name)

    def reload_version(self):
        with open("bot/__init__.py") as fin:
            for ln in fin:
                ln = ln.strip()
                if ln.startswith("__version__ = \""):
                    self.version = ln[len("__version__ = \""):-1]
                    return

    async def get_or_fetch_user(self, uid: int) -> discord.User | None:
        if uid < 10000:
            return None

        try:
            usr = self.get_user(uid)
            if not usr:
                usr = await self.fetch_user(uid)
            return usr
        except (discord.NotFound, discord.HTTPException):
            return None


if __name__ == '__main__':
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    data_path = Path(DATA_PATH)
    data_path.mkdir(parents=True, exist_ok=True)

    MaplistBot().run(TOKEN, log_level=logging.ERROR)
