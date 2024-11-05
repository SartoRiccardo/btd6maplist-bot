import discord


def composite_views(*views: discord.ui.View):
    new_view = discord.ui.View()
    for i, vw in enumerate(views):
        for item in vw.children:
            item.row = i
            new_view.add_item(item)
    return new_view


def roles_overlap(user: discord.Member, allowed_roles: list[int]) -> bool:
    for role in user.roles:
        if role.id in allowed_roles:
            return True
    return False
