import asyncio
import discord
from discord.ext import commands, tasks
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from datetime import datetime, timedelta
from typing import Any, Literal
import os
from bot.utils.env_transforms import get_nk_preview_proxy
from bot.utils.colors import EmbedColor
from bot.utils.requests.ninjakiwi import get_btd6_custom_map
from bot.utils.requests.maplist import get_maplist_user, get_formats
from bot.exceptions import MaplistResNotFound


_MAP_MOD_PERMISSIONS = {
    "create:map", "edit:map", "delete:map",
    "create:map_submission", "edit:map_submission", "delete:map_submission",
}

_FORMAT_IDS = {"Maplist": 1, "Expert List": 51}


def _has_mod_permission(permissions: dict[str, list[int | None]], format_id: int) -> bool:
    return any(
        perm in _MAP_MOD_PERMISSIONS and (None in fmts or format_id in fmts)
        for perm, fmts in permissions.items()
    )


class AdminUtilsCog(CogBase):
    close_voting_after = timedelta(seconds=3600*36)
    help_descriptions = {
        "leaderboard": "Get the Maplist leaderboard. You can choose format and page.",
    }

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.votes_expire: dict[int, tuple[datetime, int]] = {}

    async def parse_state(self, saved_at: datetime, state: dict[str, Any]) -> None:
        self.votes_expire = {}
        for msg_id in state:
            self.votes_expire[int(msg_id)] = (
                datetime.fromtimestamp(state[msg_id]["expire"]),
                state[msg_id]["channel_id"],
            )

    async def serialize_state(self) -> dict[str, Any]:
        return {
            str(msg_id): {
                "expire": int(self.votes_expire[msg_id][0].timestamp()),
                "channel_id": self.votes_expire[msg_id][1],
            }
            for msg_id in self.votes_expire
        }

    async def cog_load(self) -> None:
        await super().cog_load()
        self.task_check_vote_results.start()

    async def cog_unload(self) -> None:
        await super().cog_unload()
        self.task_check_vote_results.stop()

    @tasks.loop(seconds=60)
    async def task_check_vote_results(self):
        now = datetime.now()
        msg_ids = list(self.votes_expire.keys())
        for msg_id in msg_ids:
            expires_at, vote_ch_id = self.votes_expire[msg_id]
            if now < expires_at:
                continue

            await self.finalize_vote(vote_ch_id, msg_id)
            del self.votes_expire[msg_id]

    async def finalize_vote(self, channel_id: int, msg_id: int) -> None:
        channel: discord.TextChannel = await self.bot.fetch_channel(channel_id)
        try:
            message = await channel.fetch_message(msg_id)
        except (discord.NotFound, discord.Forbidden):
            return

        if len(message.embeds) == 0:
            return

        result = 0
        for reaction in message.reactions:
            if str(reaction) == "✅":
                result += reaction.count
            elif str(reaction) == "❌":
                result -= reaction.count
        color = EmbedColor.tie
        if result > 0:
            color = EmbedColor.success
        if result < 0:
            color = EmbedColor.fail

        embed = message.embeds[0].copy()
        embed.colour = color
        await message.edit(
            content=message.content,
            embed=embed,
        )
        await message.unpin()

    @discord.app_commands.guilds(int(os.environ["MAPLIST_GID"]))
    @discord.app_commands.command(
        name="map-vote",
        description="Call other moderators to vote on a map",
    )
    @discord.app_commands.describe(
        map_code="The map code to check",
        map_preview="An arbitrary image to call the vote on",
        silent="Whether the command should ping or not"
    )
    @autodoc
    async def cmd_map_vote(
            self,
            interaction: discord.Interaction,
            game_format: Literal["Maplist", "Expert List"],
            map_code: str = None,
            map_preview: discord.Attachment = None,
            silent: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        format_id = _FORMAT_IDS[game_format]
        user_data, formats = await asyncio.gather(
            get_maplist_user(interaction.user.id, include=["permissions"]),
            get_formats(),
            return_exceptions=True,
        )
        permissions = user_data["permissions"] if not isinstance(user_data, BaseException) else {}

        if not _has_mod_permission(permissions, format_id):
            return await interaction.edit_original_response(
                content=f"You are not a {game_format} Moderator!",
            )

        fmt = next(f for f in formats if f["id"] == format_id)
        vote_ch_id = fmt["discord_vote_channel_id"]
        vote_role_id = fmt["discord_vote_channel_ping_role_id"]
        vote_ch = await self.bot.fetch_channel(int(vote_ch_id))

        if map_code is None and map_preview is None:
            return await interaction.edit_original_response(
                content="You must either provide a `map_code` or a `map_preview`!",
            )

        if map_preview is None and (await get_btd6_custom_map(map_code)) is None:
            return await interaction.edit_original_response(
                content=f"There is no map with code {map_code}",
            )

        embed_url = map_preview.url if map_preview is not None else get_nk_preview_proxy(map_code)

        description = f"<@{interaction.user.id}> wants you to vote on this map!"
        if map_code is not None:
            description += f" (Code: `{map_code}`)"

        embed = discord.Embed(
            description=description,
            color=EmbedColor.pending,
        )
        embed.set_image(url=embed_url)

        message = await vote_ch.send(
            content=f"<@&{vote_role_id}>\n",
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none() if silent else discord.AllowedMentions.all(),
        )
        msg_url = f"https://discord.com/channels/{os.environ['MAPLIST_GID']}/{vote_ch_id}/{message.id}"

        await interaction.edit_original_response(
            content=f"You successfully [called a vote]({msg_url})!",
        )

        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await message.pin()

        self.votes_expire[message.id] = (
            datetime.now() + self.close_voting_after,
            vote_ch_id,
        )
        await self._save_state()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminUtilsCog(bot))
