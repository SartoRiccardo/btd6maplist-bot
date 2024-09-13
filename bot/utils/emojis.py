

class BaseEmjClass:
    @classmethod
    def get(cls, emname):
        return getattr(cls, emname)


class EmjIcons(BaseEmjClass):
    casual = "<:i_casual:1284134327256616960>"
    medium = "<:i_medium:1284134377155989506>"
    hard = "<:i_hard:1284134361310036018>"
    true = "<:i_true:1284134406432493569>"
    packs = "<:i_packs:1284134393585336331>"

    curver = "<:i_curver:1284134344860106775>"
    allver = "<:i_allver:1284134312664633374>"
    experts = hard


class Medals(BaseEmjClass):
    win = "<:m_win:1284093064247246921>"
    bb = "<:m_bb:1284092992294092810>"
    no_opt_hero = "<:m_noopthero:1284093053321089116>"
    lcc = "<:m_lcc:1284093037391253526>"


class Heros(BaseEmjClass):
    pass
