import discord


def composite_views(*views: discord.ui.View):
    new_view = discord.ui.View()
    for i, vw in enumerate(views):
        for item in vw.children:
            item.row = i
            new_view.add_item(item)
    return new_view
