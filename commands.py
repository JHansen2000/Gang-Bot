import os
from discord import Interaction, TextStyle, ui
import gspread
import logger
from sheets import connect
log = logger.Logger()

def get_commands(tree, guild):
    @tree.command (
        name="ping",
        description="Ping Gang Bot!",
        guild=guild,
    )
    async def ping(interaction: Interaction) -> None:
        await interaction.response.send_message("Pong!")

    @tree.command (
        name="pong",
        description="Pong Gang Bot!",
        guild=guild,
    )
    async def pong(interaction: Interaction) -> None:
        await interaction.response.send_message("Ping!")

    @tree.command (
        name="test",
        description="test sheets api",
        guild=guild,
    )
    async def test(interaction: Interaction) -> None:
        wks = await connect("Example")
        if not wks:
            await interaction.response.send_message("Sorry! I was unable to connect to the spreadsheet")
            return
        # wks.sheet1.update('B1', str(int(wks.sheet1.get('B1')[0][0]) + 1))
        wks.sheet1.update('B1', 'Bingo!')
        await interaction.response.send_message(wks.sheet1.get('A1:B1'))



# class LoginSheets(ui.Modal, title="login"):
#     name = ui.TextInput(
#         label='Name',
#         placeholder='Your name here...',.
#     )
#     feedback = ui.TextInput(
#         label='What do you think of this new feature?',
#         style=TextStyle.long,
#         placeholder='Type your feedback here...',
#         required=False,
#         max_length=300,
#     )