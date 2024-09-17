

class BaseEmjClass:
    @classmethod
    def get(cls, emname):
        return getattr(cls, emname)


class EmjIcons(BaseEmjClass):
    casual = "🙂"
    medium = "😌"
    hard = "😏"
    true = "😈"
    packs = "📦"

    curver = "⏰"
    allver = "🕰️"
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
