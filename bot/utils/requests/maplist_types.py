from typing import Any, Literal, TypedDict


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

class UserRef(TypedDict):
    name: str


class MapRef(TypedDict):
    name: str
    code: str


class LccData(TypedDict):
    leftover: int


# ---------------------------------------------------------------------------
# Full map  (get_maplist_map)
# ---------------------------------------------------------------------------

class GameRef(TypedDict):
    id: int


class RemakeOf(TypedDict):
    name: str
    game: GameRef


class Creator(TypedDict):
    name: str
    role: str | None


class Verification(TypedDict):
    name: str
    version: str | None  # truthy = current version


class MapCompletion(TypedDict):
    users: list[UserRef]
    format: int
    black_border: bool
    no_geraldo: bool
    current_lcc: bool
    subm_proof_img: list[str]
    lcc: LccData


class FullMap(TypedDict):
    code: str
    name: str
    aliases: list[str]
    map_preview_url: str
    placement_curver: int | None
    placement_allver: int | None
    difficulty: int | None       # expert difficulty index 0-4
    botb_difficulty: int | None  # BotB difficulty index 0-4
    remake_of: RemakeOf | None
    optimal_heros: list[str]
    creators: list[Creator]
    verifications: list[Verification]
    lccs: list[MapCompletion]
    r6_start: str | None


# ---------------------------------------------------------------------------
# Slim map  (get_experts, get_maplist, get_botb)
# format_idx is a plain int: position rank for maplist, difficulty index for experts/botb
# ---------------------------------------------------------------------------

class SlimMap(TypedDict):
    code: str
    name: str
    format_idx: int


# ---------------------------------------------------------------------------
# Nostalgia pack  (get_nostalgia_pack)
# format_idx is a nested object here, not an int like SlimMap
# ---------------------------------------------------------------------------

class NPCategory(TypedDict):
    id: int
    name: str


class NPFormatIdx(TypedDict):
    name: str        # original game map name
    sort_order: int
    category: NPCategory


class NPMap(TypedDict):
    code: str | None  # None/empty = map not present in BTD6
    format_idx: NPFormatIdx


# ---------------------------------------------------------------------------
# Retro maps  (get_retro_maps)
# as_list=True  -> list[RetroMap]  (game key injected by the function itself)
# as_list=False -> dict[str, dict[str, list[RetroMap]]]  (raw API shape)
# ---------------------------------------------------------------------------

class RetroMap(TypedDict):
    name: str
    id: int
    game: str  # injected by get_retro_maps; the outer game key from the API dict


# ---------------------------------------------------------------------------
# Map completions  (get_map_completions)
# NOTE: the function is annotated -> list but actually returns a paginated dict
# ---------------------------------------------------------------------------

class MapCompletionEntry(TypedDict):
    users: list[UserRef]
    format: int
    black_border: bool
    no_geraldo: bool
    current_lcc: bool


class MapCompletionsPage(TypedDict):
    total: int
    completions: list[MapCompletionEntry]


# ---------------------------------------------------------------------------
# Formats  (get_formats)
# ---------------------------------------------------------------------------

class FormatData(TypedDict):
    id: int
    hidden: bool
    emoji: str
    name: str
    run_submission_wh: str | None
    map_submission_wh: str | None
    run_submission_status: str   # "open" | "closed" | ...
    map_submission_status: str   # "open" | "open_chimps" | "closed" | ...
    proposed_difficulties: list[str] | None


# ---------------------------------------------------------------------------
# Config  (get_maplist_config)
# ---------------------------------------------------------------------------

class ConfigEntry(TypedDict):
    value: Any  # int | float | None depending on the key


class MaplistConfig(TypedDict):
    map_count: ConfigEntry
    points_bottom_map: ConfigEntry
    points_top_map: ConfigEntry
    formula_slope: ConfigEntry
    decimal_digits: ConfigEntry


# ---------------------------------------------------------------------------
# Leaderboard  (get_leaderboard)
# ---------------------------------------------------------------------------

class LeaderboardEntryUser(TypedDict):
    name: str


class LeaderboardEntry(TypedDict):
    position: int
    user: LeaderboardEntryUser
    score: float


class LeaderboardPage(TypedDict):
    pages: int
    total: int
    entries: list[LeaderboardEntry]


# ---------------------------------------------------------------------------
# User profile  (get_maplist_user)
# ---------------------------------------------------------------------------

class UserStatDetails(TypedDict):
    points: float
    pts_placement: int
    lccs: float
    lccs_placement: int
    no_geraldo: float
    black_border: float


class UserListStat(TypedDict):
    format_id: int
    stats: UserStatDetails


class UserMedals(TypedDict):
    wins: int


class UserPermission(TypedDict):
    format: int | None
    permissions: list[str]


class MaplistUser(TypedDict):
    list_stats: list[UserListStat]
    created_maps: list[Any]
    medals: UserMedals
    avatarURL: str | None
    bannerURL: str | None
    has_seen_popup: bool
    permissions: list[UserPermission]


# ---------------------------------------------------------------------------
# User completions  (get_user_completions)
# ---------------------------------------------------------------------------

class UserCompletionMap(TypedDict):
    name: str
    code: str


class UserCompletion(TypedDict):
    format: int
    no_geraldo: bool
    current_lcc: bool
    black_border: bool
    map: UserCompletionMap


class UserCompletionsPage(TypedDict):
    total: int
    completions: list[UserCompletion]


# ---------------------------------------------------------------------------
# Linked role updates  (get_linked_role_updates)
# ---------------------------------------------------------------------------

class LinkedRoleUpdate(TypedDict):
    role_id: str
    guild_id: str
    user_id: str
    action: Literal["ADD", "DEL"]
