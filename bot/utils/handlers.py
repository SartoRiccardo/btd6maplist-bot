import discord
import io
import traceback


async def handle_error(
        interaction: discord.Interaction,
        error: Exception,
) -> None:
    thrown_error = error.__cause__
    error_type = type(error.__cause__)
    if error.__cause__ is None:
        error_type = type(error)
        thrown_error = error

    if error_type == discord.app_commands.errors.MissingPermissions:
        content = "You don't have the perms to execute this command. Sorry!\n" \
                  f"*Needs permissions: {', '.join(thrown_error.missing_permissions)}*"
    elif hasattr(thrown_error, "formatted_exc"):
        content = thrown_error.formatted_exc()
        print(error)
    else:
        content = f"Error occurred: {error_type}"
        str_traceback = io.StringIO()
        traceback.print_exception(error, file=str_traceback)
        print(f"\n{str_traceback.getvalue().rstrip()}\n")

    if interaction.response.is_done():
        await interaction.edit_original_response(content=content)
    else:
        await interaction.response.send_message(content, ephemeral=True)
