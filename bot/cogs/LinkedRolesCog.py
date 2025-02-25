import discord
from discord.ext import commands, tasks
from bot.cogs.CogBase import CogBase
from datetime import datetime
from bot.utils.requests.maplist import (
    get_linked_role_updates,
    confirm_linked_role_updates,
)


class LinkedRolesCog(CogBase):
    REFRESH_EVERY = 15*60

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.next_update = datetime.fromtimestamp(
            (datetime.now().timestamp() // self.REFRESH_EVERY + 1) * self.REFRESH_EVERY
        )

    async def cog_load(self) -> None:
        await super().cog_load()
        self.task_update_linked_roles.start()

    @tasks.loop(seconds=60)
    async def task_update_linked_roles(self) -> None:
        now = datetime.now()
        if now < self.next_update:
            return
        self.next_update = datetime.fromtimestamp(
            (now.timestamp() // self.REFRESH_EVERY + 1) * self.REFRESH_EVERY
        )

        updates = await get_linked_role_updates()
        guilds = {}
        members = {}
        bad_roles = set()
        for u in updates:
            role = discord.Object(int(u["role_id"]))
            if role is bad_roles:
                continue

            if u["guild_id"] not in guilds:
                guild = await self.bot.get_or_fetch_guild(u["guild_id"])
                guilds[u["guild_id"]] = guild
            guild = guilds[u["guild_id"]]
            if guild is None:
                continue

            member_key = f"{u['user_id']}-{u['guild_id']}"
            if member_key not in members:
                try:
                    uid = int(u["user_id"])
                    members[member_key] = guild.get_member(uid)
                    if members[member_key] is None:
                        members[member_key] = await guild.fetch_member(uid)
                except (discord.NotFound, discord.HTTPException):
                    members[member_key] = None
            member = members[member_key]
            if member is None:
                continue

            try:
                if u["action"] == "ADD":
                    await member.add_roles(role)
                elif u["action"] == "DEL":
                    await member.add_roles(role)
            except (discord.Forbidden, discord.HTTPException):
                bad_roles.add(role)

        await confirm_linked_role_updates()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LinkedRolesCog(bot))
