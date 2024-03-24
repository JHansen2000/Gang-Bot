from discord import Interaction, TextStyle, ui
import sheets
import logger
log = logger.Logger()

def get_commands(tree, guild):
    @tree.command (
        name="ping",
        description="Ping Gang Bot!",
        guild=guild,
    )
    async def ping(interaction: Interaction):
        await interaction.response.send_message("Pong!")

    @tree.command (
        name="pong",
        description="Pong Gang Bot!",
        guild=guild,
    )
    async def pong(interaction: Interaction):
        await interaction.response.send_message("Ping!")

    @tree.command (
        name="test",
        description="test sheets api",
        guild=guild,
    )
    async def test(interaction: Interaction):
        try:
            temp = sheets.main()
            print("\n\n", temp, "\n\n")
            await interaction.response.send_message("done")
        except Exception as e:
            log.fatal("Sheet login failed\n\n", e)
            exit()

class LoginSheets(ui.Modal, title="login"):
    name = ui.TextInput(
        label='Name',
        placeholder='Your name here...',
    )
    feedback = ui.TextInput(
        label='What do you think of this new feature?',
        style=TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        max_length=300,
    )