import discord
from config import APP_ID, GH_REPO, BOT_NAME, EMBED_CLR
from discord.ext import commands
from bot.cogs.CogBase import CogBase


class UtilsCog(CogBase):
    help_descriptions = {
        "invite": "Invite the bot to your server!",
        "info": "General info about the bot.",
    }

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @discord.app_commands.command(name="help",
                                  description="Get info about the bot's commands.")
    @discord.app_commands.describe(module="The module to get info for.")
    async def cmd_send_help_msg(self, interaction: discord.Interaction, module: str = None) -> None:
        help_cmd = await self.bot.get_app_command("help")

        if module is None:
            cogs = self.get_help_cogs()
            cog_list = '`\n- `'.join(cogs)
            message = "This bot has many features, organized into \"modules\"! " \
                      "If you want info about a specific module, pass its name through the `module` " \
                      f"parameter the next time you use </help:{help_cmd.id}>!\n" \
                      f"*Available modules:*\n- `{cog_list}`"
            await interaction.response.send_message(message, ephemeral=True)
            return

        module = module.lower()
        cog = None
        for cog_name in self.bot.cogs.keys():
            if cog_name.lower().replace("cog", "") == module:
                cog = self.bot.cogs[cog_name]
                break

        if cog is None:
            message = f"No module named `{module}`! Please use </help:{help_cmd.id}> with no parameters " \
                      "to see which modules are available!"
            await interaction.response.send_message(message, ephemeral=True)
            return

        await interaction.response.send_message(await cog.help_message(), ephemeral=True)

    @cmd_send_help_msg.autocomplete("module")
    async def autoc_tag_tag_name(self,
                                 _interaction: discord.Interaction,
                                 current: str
                                 ) -> list[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=tag, value=tag)
            for tag in self.get_help_cogs() if current.lower() in tag.lower()
        ]

    def get_help_cogs(self):
        return [
            cog.replace("Cog", "").title()
            for cog in self.bot.cogs.keys()
            if isinstance(self.bot.cogs[cog], CogBase) and self.bot.cogs[cog].has_help_msg
        ]

    @discord.app_commands.command(name="github",
                                  description="Get the bot's repo")
    async def cmd_github(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(GH_REPO)

    @discord.app_commands.command(name="invite",
                                  description=f"Invite {BOT_NAME} to your server!")
    async def cmd_invite(self, interaction: discord.Interaction) -> None:
        perms = discord.Permissions(
            embed_links=True,
            attach_files=True,
            use_external_emojis=True,
            add_reactions=True,
        )
        url = f"https://discord.com/api/oauth2/authorize?" \
              f"client_id={APP_ID}" \
              f"&permissions={perms.value}" \
              f"&scope=bot" \
              f"&integration_type=0"
        await interaction.response.send_message(
            content=f"Wanna invite me to your server? Use [this invite link]({url})!"
        )

    @discord.app_commands.command(name="info",
                                  description="General information about the bot.")
    async def cmd_info(self, interaction: discord.Interaction) -> None:
        lr = int(self.bot.last_restart.timestamp())
        embed = discord.Embed(
            title=BOT_NAME,
            description=f"- Version: **__{self.bot.version}__**\n"
                        f"- Last Restart: <t:{lr}> (<t:{lr}:R>)\n" +
                        (
                            f"Found a bug? Yell at the maintainer or make [an issue on Github]({GH_REPO})!"
                            if len(GH_REPO) else ""
                        ) +
                        f"\n\n-# Bot and website by __Chime__ (@chimenea.mo)",
            color=EMBED_CLR,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UtilsCog(bot))
