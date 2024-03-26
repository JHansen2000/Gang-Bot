import os
from discord import Interaction, Member
from gspread_dataframe import set_with_dataframe
import gspread
import logger
from sheets import connect
from utility import get_power
import pandas as pd
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
        worksheet = await connect("Example")
        if not worksheet:
            await interaction.response.send_message("Sorry! I was unable to connect to the spreadsheet")
            return
        values = worksheet.get_values()
        dataframe = pd.DataFrame(values[1:], columns=values[0])
        # dataframe = pd.read_csv("data.txt")
        dataframe.iloc[3, 1] = int(dataframe.iloc[3, 1]) + 1 # type: ignore
        set_with_dataframe(worksheet, dataframe)
        # dataframe.to_csv('data.txt', index=False)
        await interaction.response.send_message('```' + dataframe.to_string() + '```')

    @tree.command (
        name="user",
        description="how do I send a user to the server?",
        guild=guild,
    )
    async def user(interaction: Interaction, member: Member) -> None:
        """Does something

        Parameters
        -----------
        member: discord.Member
            the member to interact with
        """
        await interaction.response.send_message(get_power(member))



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