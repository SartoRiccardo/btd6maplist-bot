import math


def points(idx: int, config: dict) -> float:
    btm = config['points_bottom_map']
    top = config['points_top_map']
    slp = config['formula_slope']
    amt = config['map_count']
    result = btm + (top/btm) ** ((1 + ((1-idx)/(amt-1))) ** slp)
    round_to = config['decimal_digits']
    return round(result, round_to) if round_to else math.floor(result)
