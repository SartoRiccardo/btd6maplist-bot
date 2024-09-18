import asyncio
import discord
from discord.ext import commands
from bot.utils.requests.maplist import get_maplist_map, get_maplist_config
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.views import VPages
from config import WEB_BASE_URL, EMBED_CLR, NK_PREVIEW_PROXY
from bot.types import EmbedPage
from bot.utils.emojis import EmjHeros, EmjIcons, EmjMisc, EmjMedals
from bot.utils.formulas import points


class MapInfoCog(CogBase):
    help_descriptions = {
        "map": "Overview of list map.\nYou can pass as a parameter the code, the Maplist position, "
               "the map name, or an alias. *This works for all commands that ask for a map.*",
        "lcc": "Get the current LCC for a map.",
        "start": "Small guide on how to start on a map (if any)",
    }

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @discord.app_commands.command(
        name="map",
        description="Information about a map",
    )
    @autodoc
    async def cmd_map(
            self,
            interaction: discord.Interaction,
            map_id: str,
            hide: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=hide)
        await self.send_map_info_messages(interaction, map_id, 0)

    @discord.app_commands.command(
        name="lcc",
        description="Information about a map's LCC run(s)",
    )
    @autodoc
    async def cmd_lcc(
            self,
            interaction: discord.Interaction,
            map_id: str,
            hide: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=hide)
        await self.send_map_info_messages(interaction, map_id, 1)

    @discord.app_commands.command(
        name="start",
        description="Information about a map's Round 6 start, if any",
    )
    @autodoc
    async def cmd_r6_start(
            self,
            interaction: discord.Interaction,
            map_id: str,
            hide: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=hide)
        await self.send_map_info_messages(interaction, map_id, 2)

    @staticmethod
    async def send_map_info_messages(
            interaction: discord.Interaction,
            map_id: str,
            idx: int
    ) -> None:
        map_data, ml_config = await asyncio.gather(
            get_maplist_map(map_id),
            get_maplist_config(),
        )

        if map_data["map_preview_url"].startswith("https://data.ninjakiwi.com"):
            map_data["map_preview_url"] = NK_PREVIEW_PROXY(map_data["code"])

        max_lcc = map_data["lccs"][0] if len(map_data["lccs"]) else None
        for lcc in map_data["lccs"]:
            if lcc["lcc"]["leftover"] > max_lcc["lcc"]["leftover"]:
                max_lcc = lcc

        pages = [
            MapInfoCog.get_map_message(map_data, ml_config),
            MapInfoCog.get_lcc_message(map_data, max_lcc),
            MapInfoCog.get_r6start_message(map_data),
        ]

        await interaction.edit_original_response(
            content=pages[idx][2],
            embeds=pages[idx][3] if pages[idx][3] else [],
            view=VPages(interaction, pages),
        )

    @staticmethod
    def get_map_message(
            map_data: dict,
            ml_config: dict
    ) -> EmbedPage:
        description = ""
        if len(map_data["aliases"]):
            description += f"-# Aliases: {' - '.join(map_data['aliases'])}\n"

        diff_parts = []
        if map_data["difficulty"] != -1:
            diff_str = ["Casual", "Medium", "Hard", "True"][map_data["difficulty"]]
            diff_parts.append(
                f"{EmjIcons.diff_by_index(map_data['difficulty'])} {diff_str} Expert"
            )
        if map_data["placement_cur"] != -1:
            diff_parts.append(
                f"{EmjIcons.curver} #{map_data['placement_cur']} ({points(map_data['placement_cur'], ml_config)}pt)"
            )
        # if map_data["placement_all"] != -1:
        #     diff_parts.append(
        #         f"{EmjIcons.allver} #{map_data['placement_all']} ({points(map_data['placement_cur'], ml_config)}pt)"
        #     )
        if len(diff_parts):
            description += " / ".join(diff_parts) + "\n"

        if len(map_data["optimal_heros"]):
            hero_emojis = [EmjHeros.get(hr) for hr in map_data["optimal_heros"]]
            description += f"\n**Optimal Heros**\n" \
                           f"# {' '.join(hero_emojis)}\n"

        embed = discord.Embed(
            color=EMBED_CLR,
            title=map_data["name"],
            description=description,
            url=f"{WEB_BASE_URL}/map/{map_data['code']}",
        )
        embed.set_image(url=map_data["map_preview_url"])
        embed.set_author(name=map_data["code"])
        embed.add_field(
            name="Creator" + ("s" if len(map_data["creators"]) > 1 else ""),
            value="\n".join(
                (f"- {creator['name']}" + ("" if not creator["role"] else f" *({creator['role']})*"))
                for creator in map_data["creators"]
            ),
            inline=True,
        )
        if len(map_data["verifications"]):
            embed.add_field(
                name="Verifier" + ("s" if len(map_data["creators"]) > 1 else ""),
                value="\n".join(
                    (f"- {verif['name']}" + ("" if not verif["version"] else " *(Current ver)*"))
                    for verif in map_data["verifications"]
                ),
                inline=True,
            )
        return "🗺️", "Map Overview", None, [embed]

    @staticmethod
    def get_lcc_message(
            map_data: dict,
            lcc_data: dict | None,
    ) -> EmbedPage:
        emj = "<:m_lcc:1284093037391253526>"
        label = "Least Cash CHIMPS"
        if lcc_data is None:
            return emj, label, "-# No LCCs for this map!", None

        is_proof_image = lcc_data["lcc"]["proof"] and \
            any([
                lcc_data["lcc"]["proof"].endswith(f".{ext}")
                for ext in ["jpg", "jpeg", "webp", "png"]
            ])

        ply_list = lcc_data["users"][0]["name"] \
            if len(lcc_data["users"]) == 1 else \
            "\n".join([f"- {usr['name']}" for usr in lcc_data["users"]])

        format_emj = EmjIcons.format(lcc_data["format"])
        medals = [
            EmjMedals.bb if lcc_data["black_border"] else EmjMedals.win,
            EmjMedals.no_opt_hero if lcc_data["no_geraldo"] else None,
            EmjMedals.lcc,
        ]
        medals_str = " ".join([mdl for mdl in medals if mdl is not None])

        embed = discord.Embed(
            color=EMBED_CLR,
            title="Least Cash CHIMPS",
            description=f"{format_emj} / {medals_str}\n"
                        f"Saveup: {EmjMisc.cash} **{lcc_data['lcc']['leftover']:,}**",
            url=None if is_proof_image else lcc_data["lcc"]["proof"],
        )
        embed.set_author(
            name=map_data["name"],
            url=f"{WEB_BASE_URL}/map/{map_data['code']}",
        )
        if is_proof_image:
            embed.set_image(url=lcc_data["lcc"]["proof"])
        embed.add_field(
            name="Player" + ("s" if len(lcc_data["users"]) > 1 else ""),
            value=ply_list,
        )

        return emj, label, None, [embed]

    @staticmethod
    def get_r6start_message(
            map_data: dict,
    ) -> EmbedPage:
        emj = "🎯"
        label = "Round 6 Start"
        if map_data["r6_start"] is None:
            return emj, label, "-# No R6 Start info for this map!", None

        content = f"Round 6 Start for [{map_data['name']}]({WEB_BASE_URL}/map/{map_data['code']}):\n" + \
                  map_data["r6_start"]
        return emj, label, content, None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MapInfoCog(bot))
