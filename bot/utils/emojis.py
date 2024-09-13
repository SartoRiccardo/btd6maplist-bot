

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

    @classmethod
    def diff_by_index(cls, idx: int) -> str:
        return [cls.casual, cls.medium, cls.hard, cls.true][idx]

    @classmethod
    def format(cls, fmt: int) -> str | None:
        return ({
            1: cls.curver,
            2: cls.allver,
            51: cls.experts,
        }).get(fmt)


class EmjMedals(BaseEmjClass):
    win = "<:m_win:1284093064247246921>"
    bb = "<:m_bb:1284092992294092810>"
    no_opt_hero = "<:m_noopthero:1284093053321089116>"
    lcc = "<:m_lcc:1284093037391253526>"


class EmjHeros(BaseEmjClass):
    quincy = "<:h_quincy:1284204430199230534>"
    gwen = "<:h_gwen:1284204379615924244>"
    obyn = "<:h_obyn:1284204391804571759>"
    striker = "<:h_striker:1284204469709705247>"
    churchill = "<:h_churchill:1284204314151096343>"
    ben = "<:h_ben:1284204290356940914>"
    ezili = "<:h_ezili:1284204353221169233>"
    pat = "<:h_pat:1284204408309284945>"
    adora = "<:h_adora:1284204278562553957>"
    brickell = "<:h_brickell:1284204302499577879>"
    etienne = "<:h_etienne:1284204335336525856>"
    sauda = "<:h_sauda:1284204458619834448>"
    psi = "<:h_psi:1284204418924810314>"
    geraldo = "<:h_geraldo:1284204366429028423>"
    corvus = "<:h_corvus:1284204325455007940>"
    rosalia = "<:h_rosalia:1284204442270433365>"


class EmjMisc(BaseEmjClass):
    cash = ""
