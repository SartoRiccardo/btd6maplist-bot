import math


def points(idx: int, config: dict) -> float:
    btm = config['points_bottom_map']
    top = config['points_top_map']
    slp = config['formula_slope']
    amt = config['map_count']
    result = btm + (top/btm) ** ((1 + ((1-idx)/(amt-1))) ** slp)
    round_to = config['decimal_digits']
    return round(result, round_to) if round_to else math.floor(result)


def get_page_idxs(
        page: int,
        items_page: int,
        items_page_srv: int
) -> tuple[int, int, int, int]:
    start_idx = (page-1) * items_page
    end_idx = page * items_page - 1
    req_page_start = start_idx // items_page_srv + 1
    req_page_end = end_idx // items_page_srv + 1
    return start_idx, end_idx, req_page_start, req_page_end
