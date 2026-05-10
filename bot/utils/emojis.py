

class BaseEmjClass:
    @classmethod
    def get(cls, emname):
        return getattr(cls, emname)


class EmjIcons(BaseEmjClass):
    casual = "<:i_casual:1284134327256616960>"
    medium = "<:i_medium:1284134377155989506>"
    hard = "<:i_hard:1284134361310036018>"
    true = "<:i_true:1284134406432493569>"
    extreme = "<:i_extreme:1293317962953920614>"
    packs = "<:i_packs:1284134393585336331>"

    botb_beginner = "<:icon_botb_1:1361394050602762310>"
    botb_intermediate = "<:icon_botb_2:1361394005832630673>"
    botb_advanced = "<:icon_botb_3:1361394035742347285>"
    botb_expert = "<:icon_botb_4:1361393994143367461>"
    botb_extreme = "🔥"

    np_btd123 = "<:icon_np_1:1361394342157095293>"
    np_btd_console = "<:icon_np_2:1361394359744069934>"
    np_btd4 = "<:icon_np_3:1361394376491798528>"
    np_btd5 = "<:icon_np_4:1361394391901671515>"
    np_btdb = "<:icon_np_5:1361394411459707021>"
    np_bmc = "<:icon_np_6:1361394429252075692>"
    np_battd = "<:icon_np_7:1361394445148492019>"
    np_btdb2 = "<:icon_np_8:1361394456292753449>"
    np_missing = "❓"

    curver = "<:i_curver:1284134344860106775>"
    allver = "<:i_allver:1284134312664633374>"
    experts = hard
    botb_icon = "<:icon_botb:1361394250717073619>"
    np = np_btd123

    @classmethod
    def diff_by_index(cls, idx: int) -> str:
        return [cls.casual, cls.medium, cls.hard, cls.true, cls.extreme][idx]

    @classmethod
    def botb_diff_by_index(cls, idx: int) -> str:
        return [cls.botb_beginner, cls.botb_intermediate, cls.botb_advanced, cls.botb_expert, cls.botb_expert][idx]

    @classmethod
    def game(cls, idx: int) -> str:
        return [cls.np_btd123, cls.np_btd_console, cls.np_btd4, cls.np_btd5, cls.np_btdb, cls.np_bmc, cls.np_battd,
                cls.np_btdb2][idx]

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
    silas = "<:h_silas:1421227845706977400>"
    psi = "<:h_psi:1284204418924810314>"
    geraldo = "<:h_geraldo:1284204366429028423>"
    corvus = "<:h_corvus:1284204325455007940>"
    rosalia = "<:h_rosalia:1284204442270433365>"


class EmjMisc(BaseEmjClass):
    cash = "<a:cash:1148694623192105010>"
    blank = "<:_:1121392589204094976>"


class EmjPlacements(BaseEmjClass):
    top1 = "🥇"
    top2 = "🥈"
    top3 = "🥉"
