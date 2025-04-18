

class BaseEmjClass:
    @classmethod
    def get(cls, emname):
        return getattr(cls, emname)


class EmjIcons(BaseEmjClass):
    casual = "🙂"
    medium = "😌"
    hard = "😏"
    true = "😈"
    extreme = "🔥"
    packs = "📦"

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

    curver = "⏰"
    allver = "🕰️"
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
    win = "🔴"
    bb = "⚫"
    no_opt_hero = "🎖️"
    lcc = "🪙"


# In-game hero select icons
class EmjHeros(BaseEmjClass):
    quincy = "🦸‍♂️"
    gwen = "🦸‍♂️"
    obyn = "🦸‍♂️"
    striker = "🦸‍♂️"
    churchill = "🦸‍♂️"
    ben = "🦸‍♂️"
    ezili = "🦸‍♂️"
    pat = "🦸‍♂️"
    adora = "🦸‍♂️"
    brickell = "🦸‍♂️"
    etienne = "🦸‍♂️"
    sauda = "🦸‍♂️"
    psi = "🦸‍♂️"
    geraldo = "🦸‍♂️"
    corvus = "🦸‍♂️"
    rosalia = "🦸‍♂️"


class EmjMisc(BaseEmjClass):
    cash = "<a:cash:1148694623192105010>"  # BTD6 cash icon
    blank = "<:_:1121392589204094976>"  # Completely transparent emoji


class EmjPlacements(BaseEmjClass):
    top1 = "🥇"
    top2 = "🥈"
    top3 = "🥉"
