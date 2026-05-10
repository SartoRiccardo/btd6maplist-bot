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


# ---------------------------------------------------------------------------
# Full map  (get_maplist_map)
# ---------------------------------------------------------------------------

class MapUser(TypedDict):
    discord_id: str
    name: str
    is_banned: bool


class Creator(TypedDict):
    user_id: str
    role: str
    user: MapUser


class Verification(TypedDict):
    user_id: str
    version: int | None  # None = applies to all versions; int = specific BTD6 version
    user: MapUser


class CompletionLcc(TypedDict):
    leftover: int


class FullMap(TypedDict):
    code: str
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
    remake_of: int | None
    deleted_on: str | None
    is_verified: bool
    aliases: list[str]
    creators: list[Creator]
    verifications: list[Verification]
    retro_map: MapEntryRetroMap | None


# ---------------------------------------------------------------------------
# GET /maps  (get_experts, get_maplist, get_botb, get_nostalgia_pack)
# ---------------------------------------------------------------------------

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
# Completions  (get_completions, get_map_lcc)
# ---------------------------------------------------------------------------

class CompletionMapBase(TypedDict):
    code: str
    name: str
    r6_start: int | None
    map_data: str | None
    map_preview_url: str
    map_notes: str | None


class CompletionEntry(TypedDict):
    id: int
    map_code: str
    submitted_on: int
    subm_notes: str | None
    subm_proof_img: list[str]
    subm_proof_vid: list[str]
    format_id: int
    black_border: bool
    no_geraldo: bool
    deleted_on: str | None
    accepted_by: str | None
    lcc: CompletionLcc | None
    is_current_lcc: bool
    players: list[MapUser]
    map: CompletionMapBase


class CompletionsMeta(TypedDict):
    current_page: int
    last_page: int
    per_page: int
    total: int


class CompletionsPage(TypedDict):
    data: list[CompletionEntry]
    meta: CompletionsMeta


# ---------------------------------------------------------------------------
# Formats  (get_formats)
# ---------------------------------------------------------------------------

class FormatData(TypedDict):
    id: int
    name: str
    slug: str
    description: str
    button_text: str
    map_submission_rules: str
    completion_submission_rules: str
    discord_server_url: str | None
    hidden: bool
    run_submission_status: Literal["open", "closed", "lcc_only"]
    map_submission_status: Literal["open", "closed"]
    proposed_difficulties: list[str] | None
    emoji: str | None
    is_no_geraldo_enabled: bool
    is_lcc_leaderboard_enabled: bool
    is_black_border_leaderboard_enabled: bool
    is_no_geraldo_leaderboard_enabled: bool
    preview_map_1: CompletionMapBase | None
    preview_map_2: CompletionMapBase | None
    preview_map_3: CompletionMapBase | None


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
# Linked role updates  (get_linked_role_updates)
# ---------------------------------------------------------------------------

class LinkedRoleUpdate(TypedDict):
    role_id: str
    guild_id: str
    user_id: str
    action: Literal["ADD", "DEL"]
