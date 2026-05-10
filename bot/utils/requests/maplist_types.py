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
# GET /maps  (get_experts, get_maplist, get_botb, get_nostalgia_pack)
# ---------------------------------------------------------------------------

class RetroGame(TypedDict):
    id: int
    game_id: int
    category_id: int
    subcategory_id: int
    game_name: str
    category_name: str
    subcategory_name: str


class MapEntryRetroMap(TypedDict):
    id: int
    name: str
    sort_order: int
    preview_url: str
    retro_game_id: int
    game: RetroGame


class MapEntryMedals(TypedDict):
    completed: bool
    black_border: bool
    no_geraldo: bool
    current_lcc: bool


class MapEntry(TypedDict):
    code: str | None      # None on retro stub entries (fill_missing_retro=true)
    name: str
    r6_start: int | None
    map_data: str | None
    map_preview_url: str
    map_notes: str | None
    placement_curver: int | None
    placement_allver: int | None
    difficulty: int | None
    optimal_heros: list[str]
    botb_difficulty: int | None
    remake_of: int | None  # retro map ID
    deleted_on: str | None
    is_verified: bool
    retro_map: MapEntryRetroMap | None  # present when format_id=11 or remake_of != null


# ---------------------------------------------------------------------------
# Retro maps  (get_retro_maps)
# ---------------------------------------------------------------------------

class RetroMap(TypedDict):
    id: int
    name: str
    sort_order: int
    preview_url: str | None
    retro_game_id: int
    deleted_at: str | None
    game: RetroGame


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

class MaplistConfig(TypedDict):
    points_top_map: float
    points_bottom_map: float
    formula_slope: float
    points_extra_lcc: float
    points_multi_gerry: float
    points_multi_bb: float
    decimal_digits: int
    map_count: int
    current_btd6_ver: int
    exp_points_casual: float
    exp_points_medium: float
    exp_points_high: float
    exp_points_true: float
    exp_points_extreme: float
    exp_nogerry_points_casual: float
    exp_nogerry_points_medium: float
    exp_nogerry_points_high: float
    exp_nogerry_points_true: float
    exp_nogerry_points_extreme: float
    exp_bb_multi: float
    exp_lcc_extra: float


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
