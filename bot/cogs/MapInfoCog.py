import asyncio
import discord
import math
from discord.ext import commands
from bot.utils.requests.maplist import (
    get_maplist_map,
    get_map_completions,
    get_maplist_config,
    get_experts,
    get_maplist,
    get_formats,
    search_maps,
    get_botb,
    get_nostalgia_pack,
)
from bot.cogs.CogBase import CogBase
from bot.utils.decos import autodoc
from bot.utils.models import MessageContent, LazyMessageContent
from bot.views import VPages, VPaginateList
from config import WEB_BASE_URL, EMBED_CLR, NK_PREVIEW_PROXY
from bot.types import ExpertDifficulty, BotbDifficulty, NostalgiaPackGame
from bot.utils.emojis import EmjHeros, EmjIcons, EmjMisc, EmjMedals
from bot.utils.formulas import points
from bot.utils.colors import EmbedColor
from bot.utils.formulas import get_page_idxs
from bot.utils.misc import image_formats
from typing import get_args
from collections.abc import Callable
from bot.utils.discordutils import composite_views


class MapInfoCog(CogBase):
    help_descriptions = {
        "map": "Overview of a list map.\nYou can pass as a parameter the code, the Maplist position, "
               "the map name, or an alias. *This works for all commands that ask for a map.*",
        "lcc": "Get the current LCC for a map.",
        "start": "Small guide on how to start on a map (if any)",
        "experts": "List of all expert maps, by difficulty.",
        "maplist": "List all of the maps in the Maplist.",
        "best-of-the-best": "List all of the maps in the Best of the Best pack, by difficulty.",
        "nostalgia-pack": "List all of the maps in the Nostalgia Pack, by game.",
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

    @cmd_map.autocomplete("map_id")
    @cmd_lcc.autocomplete("map_id")
    @cmd_r6_start.autocomplete("map_id")
    async def autocomplete_map_id(self, _i: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=map_data["name"], value=map_data["code"])
            for map_data in await search_maps(current)
        ]

    @discord.app_commands.command(
        name="experts",
        description="Get a list of Expert maps, by difficulty",
    )
    @discord.app_commands.describe(
        difficulty="The difficulty you want to search."
    )
    @autodoc
    async def cmd_experts(
            self,
            interaction: discord.Interaction,
            difficulty: ExpertDifficulty,
            hide: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=hide)
        labels = get_args(ExpertDifficulty)
        info = [
            (EmjIcons.casual, "casual", "Easy and enjoyable, yet not brainless maps. Expect a game where many towers "
                                        "are viable. Comparable difficulty to maps like Workshop and Muddy Puddles."),
            (EmjIcons.medium, "medium", "Challenging, but not frustrating or intense difficulty. May have "
                                        "complications at any point. Comparable difficulty to maps like Sanctuary and "
                                        "Flooded Valley."),
            (EmjIcons.hard, "high", "Has at least one phase of the game that is very tough, usually a hard lategame "
                                    "at minimum. Comparable difficulty to maps like Dark Dungeons and Quad."),
            (EmjIcons.true, "true", "_If you're asking for one of the best, you'd better be one of the best._ Many "
                                    "strategies will not work. Comparable to, or even greater difficulty than maps "
                                    "like Bloody Puddles and Ouch."),
            (EmjIcons.extreme, "extreme", "The absolute hardest the community has to offer. Many strategies are "
                                          "forced, don't hesitate to go all out to beat these maps. _Good luck..._"),
        ]
        diffval = labels.index(difficulty)
        experts = await get_experts()
        experts = [exp for exp in experts if exp["format_idx"] == diffval]

        def create_message(entries: list[dict]) -> discord.Embed:
            content = "\n".join([
                f"`{exp['code']}` ｌ {exp['name']}"
                for exp in entries
            ])
            icon, diffq, desc = info[diffval]
            return discord.Embed(
                title=f"{icon} {difficulty}s",
                description=f"{desc}\n\n{content}",
                color=EmbedColor.experts,
                url=f"{WEB_BASE_URL}/experts?difficulty={diffq}",
            )

        await self.send_list(
            interaction,
            experts,
            create_message,
        )

    @discord.app_commands.command(
        name="maplist",
        description="Get the Maplist",
    )
    @autodoc
    async def cmd_maplist(
            self,
            interaction: discord.Interaction,
            hide: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=hide)
        maplist, cfg = await asyncio.gather(
            get_maplist(),
            get_maplist_config(),
        )

        def create_message(entries: list[dict]) -> discord.Embed:
            content = "\n".join([
                f"`{'#'+str(mlmap['format_idx']): >3}` (`{points(mlmap['format_idx'], cfg): >3}pt`) ｌ "
                f"`{mlmap['code']}` ｌ {mlmap['name']}"
                for mlmap in entries
            ])
            return discord.Embed(
                title=f"The Maplist",
                description=f"{content}",
                color=EmbedColor.maplist,
                url=f"{WEB_BASE_URL}/list",
            )

        await self.send_list(
            interaction,
            maplist,
            create_message,
        )

    @discord.app_commands.command(
        name="best-of-the-best",
        description="Get the Best of the Best pack",
    )
    @discord.app_commands.describe(
        difficulty="The difficulty you want to search."
    )
    @autodoc
    async def cmd_botb(
            self,
            interaction: discord.Interaction,
            difficulty: BotbDifficulty,
            hide: bool = False,
    ) -> None:
        await interaction.response.defer(ephemeral=hide)
        labels = get_args(BotbDifficulty)
        info = [
            (EmjIcons.botb_beginner, "beginner",
             "Simple, clean, and beautifully crafted — these maps are perfect for getting started or just enjoying the "
             "art of great design."),
            (EmjIcons.botb_intermediate, "intermediate",
             "These maps introduce a bit more challenge, but nothing you haven’t handled before. The gameplay stays "
             "fair and familiar, while the decoration steps things up with unique and polished visuals that bring "
             "every map to life."),
            (EmjIcons.botb_advanced, "advanced",
             "While the visuals are still top-tier, the focus here shifts to serious gameplay."),
            (EmjIcons.botb_expert, "expert",
             "Beautiful and brutal. Maps marked with a flame are extreme, they might break within updates and are "
             "sometimes featured in harder lists."),
        ]
        diffval = labels.index(difficulty)
        if diffval != 3:
            botb_list = await get_botb(diffval)
        else:
            expert, extreme = await asyncio.gather(
                get_botb(3),
                get_botb(4),
            )
            botb_list = [*expert, *extreme]

        def create_message(entries: list[dict]) -> discord.Embed:
            extr_emoji = f'  {EmjIcons.botb_extreme}'
            content = "\n".join([
                f"`{map_data['code']}` ｌ{extr_emoji if map_data['format_idx'] == 4 else ''} {map_data['name']}"
                for map_data in entries
            ])
            icon, diffq, desc = info[diffval]
            return discord.Embed(
                title=f"{icon} {difficulty}s",
                description=f"{desc}\n\n{content}",
                color=EmbedColor.botb,
                url=f"{WEB_BASE_URL}/best-of-the-best?difficulty={diffq}",
            )

        await self.send_list(
            interaction,
            botb_list,
            create_message,
        )

    @discord.app_commands.command(
        name="nostalgia-pack",
        description="Get the Nostalgia Pack",
    )
    @discord.app_commands.describe(
        game="The game you want to search for."
    )
    @autodoc
    async def cmd_np(
            self,
            interaction: discord.Interaction,
            game: NostalgiaPackGame,
            hide: bool = False,
    ) -> None:
        items_page = 10

        await interaction.response.defer(ephemeral=hide)
        labels = get_args(NostalgiaPackGame)
        info = [
            (EmjIcons.np_btd123, "btd1_2_3"),
            (EmjIcons.np_btd_console, "btd_ios_psn_dsi"),
            (EmjIcons.np_btd4, "bloons_td_4"),
            (EmjIcons.np_btd5, "bloons_td_5"),
            (EmjIcons.np_btdb, "bloons_td_battles"),
            (EmjIcons.np_bmc, "bloons_monkey_city"),
            (EmjIcons.np_battd, "bloons_adventure_time_td"),
            (EmjIcons.np_btdb2, "bloons_td_battles_2"),
        ]
        diffval = labels.index(game)
        nostalgia_pack = await get_nostalgia_pack(diffval)

        def create_message(entries: list[dict]) -> discord.Embed:
            category = entries[0]["format_idx"]["category"]["name"]
            content = "\n".join([
                (
                    f"`{map_data['code']}` ｌ {map_data['format_idx']['name']}"
                    if map_data["code"] else
                    f"`       ` ｌ ~~{map_data['format_idx']['name']}~~ {EmjIcons.np_missing}"
                )
                for map_data in entries
            ])
            icon, diffq = info[diffval]

            category_q = category.lower().replace(" ", "_")
            return discord.Embed(
                title=f"{icon} {category}",
                description=content,
                color=EmbedColor.np,
                url=f"{WEB_BASE_URL}/nostalgia-pack?game={diffq}&category={category_q}",
            )

        nostalgia_pack.sort(
            key=lambda x: (x["format_idx"]["category"]["id"], x["format_idx"]["sort_order"])
        )

        maps_by_category = {}
        for map_data in nostalgia_pack:
            maps_by_category \
                .setdefault(map_data["format_idx"]["category"]["name"], []) \
                .append(map_data)

        pages = []

        view_tabs = VPages(
            interaction,
            pages,
            placeholder=lambda page: pages[page][1],
            autoload=False,
        )

        for category, maps in maps_by_category.items():
            msg_content = MessageContent(
                embeds=create_message(maps[:items_page]),
                view=VPaginateList(
                    interaction,
                    math.ceil(len(maps) / items_page),
                    1,
                    {1: maps},
                    items_page,
                    len(maps),
                    None,
                    create_message,
                    list_key=None,
                    additional_views=[view_tabs],
                ),
            )
            pages.append((None, category, msg_content))

        view_tabs.load_items()
        await interaction.edit_original_response(
            embeds=await pages[0][2].embeds(),
            view=composite_views(
                await pages[0][2].view(),
                view_tabs,
            ),
        )

    @staticmethod
    async def send_list(
            interaction: discord.Interaction,
            map_list: list[dict],
            create_message: Callable[[list[dict]], discord.Embed],
            items_page: int = 10,
    ) -> None:
        paginate_view = VPaginateList(
            interaction,
            math.ceil(len(map_list) / items_page),
            1,
            {1: map_list},
            items_page,
            len(map_list),
            None,
            create_message,
            list_key=None,
        )
        await interaction.edit_original_response(
            embed=create_message(paginate_view.get_needed_rows(1, {1: map_list})),
            view=paginate_view,
        )

    @staticmethod
    async def send_map_info_messages(
            interaction: discord.Interaction,
            map_id: str,
            idx: int
    ) -> None:
        map_data, ml_config, ml_formats = await asyncio.gather(
            get_maplist_map(map_id),
            get_maplist_config(),
            get_formats(),
        )
        visible_formats = [f["id"] for f in ml_formats if not f["hidden"]]

        if map_data["map_preview_url"].startswith("https://data.ninjakiwi.com"):
            map_data["map_preview_url"] = NK_PREVIEW_PROXY(map_data["code"])

        max_lcc = map_data["lccs"][0] if len(map_data["lccs"]) else None
        for lcc in map_data["lccs"]:
            if lcc["lcc"]["leftover"] > max_lcc["lcc"]["leftover"]:
                max_lcc = lcc

        pages = []
        select_pages = [
            ("🗺️", "Map Overview"),
            (EmjMedals.lcc, "Least Cash CHIMPS"),
            ("🎯", "Round 6 Start"),
        ]
        page_contents = [
            MapInfoCog.get_map_message(map_data, ml_config, visible_formats),
            MapInfoCog.get_lcc_message(map_data, max_lcc),
            MapInfoCog.get_r6start_message(map_data),
        ]
        for i in range(len(select_pages)):
            pages.append((*select_pages[i], page_contents[i]))

        views_to_load = []

        comp_page_view = VPages(interaction, pages, current_page=len(select_pages), autoload=False)
        pages.append(
            (
                EmjMedals.win, "Completions",
                MapInfoCog.get_completions_message(
                    interaction,
                    map_data,
                    comp_page_view,
                )
            )
        )
        views_to_load.append(comp_page_view)

        for view in views_to_load:
            view.load_items()

        content = await pages[idx][2].content()
        embeds = await pages[idx][2].embeds()
        await interaction.edit_original_response(
            content=content,
            embeds=embeds if embeds else [],
            view=VPages(interaction, pages),
        )

    @staticmethod
    def get_map_message(
            map_data: dict,
            ml_config: dict,
            visible_formats: list[int],
    ) -> MessageContent:
        description = ""
        if len(map_data["aliases"]):
            description += f"-# Aliases: {' - '.join(map_data['aliases'])}\n"

        diff_parts = []
        if map_data["placement_curver"] is not None and \
                map_data["placement_curver"] <= ml_config['map_count']["value"] and \
                1 in visible_formats:
            diff_parts.append(
                f"{EmjIcons.curver} #{map_data['placement_curver']} ({points(map_data['placement_curver'], ml_config)}pt)"
            )
        if map_data["placement_allver"] is not None and \
                map_data["placement_allver"] <= ml_config['map_count']["value"] and \
                2 in visible_formats:
            diff_parts.append(
                f"{EmjIcons.allver} #{map_data['placement_allver']} ({points(map_data['placement_allver'], ml_config)}pt)"
            )
        if map_data["difficulty"] is not None and 51 in visible_formats:
            difficulties = get_args(ExpertDifficulty)
            diff_str = difficulties[map_data["difficulty"]]
            diff_parts.append(
                f"{EmjIcons.diff_by_index(map_data['difficulty'])} {diff_str}"
            )
        if map_data["botb_difficulty"] is not None and 52 in visible_formats:
            difficulties = list(get_args(BotbDifficulty)) + ["Expert"]
            diff_str = difficulties[map_data["botb_difficulty"]]
            diff_parts.append(
                f"{EmjIcons.botb_diff_by_index(map_data['botb_difficulty'])} {diff_str}"
            )
        if map_data["remake_of"] is not None and 11 in visible_formats:
            diff_parts.append(
                f"{EmjIcons.game(map_data['remake_of']['game']['id'])} {map_data['remake_of']['name']}"
            )
        if len(diff_parts):
            description += "".join([f"- {part}\n" for part in diff_parts])

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
        return MessageContent(embeds=[embed])

    @staticmethod
    def get_lcc_message(
            map_data: dict,
            lcc_data: dict | None,
    ) -> MessageContent:
        if lcc_data is None:
            return MessageContent(content="-# No LCCs for this map!")

        image_proofs = [
            proof_url for proof_url in lcc_data["subm_proof_img"]
            if any(proof_url.endswith(f".{ext}") for ext in image_formats)
        ]

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

        map_url = f"{WEB_BASE_URL}/map/{map_data['code']}"
        embed = discord.Embed(
            color=EMBED_CLR,
            title="Least Cash CHIMPS",
            description=f"{format_emj} / {medals_str}\n"
                        f"Saveup: {EmjMisc.cash} **{lcc_data['lcc']['leftover']:,}**",
            url=map_url,
        )
        embed.set_author(name=map_data["name"])
        if len(image_proofs):
            embed.set_image(url=image_proofs[0])
        embed.add_field(
            name="Player" + ("s" if len(lcc_data["users"]) > 1 else ""),
            value=ply_list,
        )

        embeds = [embed]
        for proof_url in image_proofs[1:4]:
            embed = discord.Embed(url=map_url)
            embed.set_image(url=proof_url)
            embeds.append(embed)

        return MessageContent(embeds=embeds)

    @staticmethod
    def get_r6start_message(
            map_data: dict,
    ) -> MessageContent:
        if map_data["r6_start"] is None:
            return MessageContent(content="-# No R6 Start info for this map!")

        content = f"Round 6 Start for [{map_data['name']}]({WEB_BASE_URL}/map/{map_data['code']}):\n" + \
                  map_data["r6_start"]
        return MessageContent(content=content)

    @staticmethod
    def get_completions_message(
            interaction: discord.Interaction,
            map_data: dict,
            pages_view: VPages,
    ) -> MessageContent:
        items_page = 12
        items_page_srv = 50
        _si, _ei, req_page_start, req_page_end = get_page_idxs(1, items_page, items_page_srv)

        async def request_completions(pages: list[int]):
            lb_data = await asyncio.gather(*[
                get_map_completions(map_data["code"], pg)
                for pg in pages
            ])
            return {pg: lb_data[i] for i, pg in enumerate(pages)}

        def build_message(entries: list[dict]) -> str:
            if len(entries) == 0:
                return f"## {map_data['name']} — Completions\n\n" \
                       f"-# Not much going on here... you could LCC this map by default!"

            row_template = "`{: <20}`  |  {}\n"
            medals_template = "{}  ~  {}"
            content = f"## {map_data['name']} — Completions\n" \
                      "User                                         |  Format ~ Medals\n" \
                      "—————————————  +  —————————\n"
            for entry in entries:
                for i, ply in enumerate(entry["users"]):
                    comp_format_emj = EmjIcons.format(entry["format"])
                    comp_medals = [EmjMedals.bb if entry["black_border"] else EmjMedals.win]
                    if entry["format"] <= 50 and entry["no_geraldo"]:
                        comp_medals.append(EmjMedals.no_opt_hero)
                    if entry["current_lcc"]:
                        comp_medals.append(EmjMedals.lcc)
                    comp_info = "↓     ↓     ↓     ↓" if i < len(entry["users"])-1 else \
                        medals_template.format(comp_format_emj, " ".join(comp_medals))
                    uname = ply["name"]
                    if len(uname) > 20:
                        uname = f"{uname[:20]}+"
                    content += row_template.format(uname, comp_info)
            return content.strip()

        async def load_message() -> MessageContent:
            pages_to_req = [pg for pg in range(req_page_start, req_page_end+1)]
            comp_pages = await request_completions(pages_to_req)

            client_pages = math.ceil(comp_pages[req_page_start]["total"] / items_page)
            view = VPaginateList(
                interaction,
                client_pages,
                1,
                comp_pages,
                items_page,
                items_page_srv,
                request_completions,
                build_message,
                additional_views=[pages_view],
                list_key="completions",
            )
            return MessageContent(
                content=view.message_on_page(1),
                view=view,
            )

        return LazyMessageContent(load_message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MapInfoCog(bot))
