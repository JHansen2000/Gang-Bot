from discord import Interaction, Member, Role, Client, Object, app_commands
from sheets import get_worksheet, create_worksheet, delete_worksheet, get_worksheets
from utility import delete_role, get_guild, get_power, can_execute, new_role
import string
import pandas as pd
import logger
log = logger.Logger()

def get_commands(client: Client, tree: app_commands.CommandTree[Client], guild_id: int):
    guild = Object(guild_id)

    @tree.command (
        name="ping",
        description="Ping Gang Bot!",
        guild=guild,
    )
    async def ping(interaction: Interaction) -> None:
        log.info("Command Received: ping")
        if not can_execute(interaction.user, 1, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return
        await interaction.response.send_message("Pong!")

    @tree.command (
        name="pong",
        description="Pong Gang Bot!",
        guild=guild,
    )
    async def pong(interaction: Interaction) -> None:
        log.info("Command Received: pong")
        if not can_execute(interaction.user, 1, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return
        await interaction.response.send_message("Ping!")

    @tree.command (
        name="test",
        description="test sheets api",
        guild=guild,
    )
    async def test(interaction: Interaction, gang_role: Role) -> None:
        """Does something

        Parameters
        -----------
        gang_role: discord.Role
            The role of the gang to get the roster for
        """
        log.info("Command Received: test")
        if not can_execute(interaction.user, 2, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return
        worksheet = get_worksheet(gang_role.name)
        if not worksheet:
            await interaction.response.send_message(f"There is no roster for {gang_role.name}\nThis is probably a major error, try to repair with `/repair`")
            return
        values = worksheet.get_values()
        dataframe = pd.DataFrame(values[1:], columns=values[0])

        # dataframe = pd.read_csv("data.txt")
        # dataframe.iloc[3, 1] = int(dataframe.iloc[3, 1]) + 1 # type: ignore
        # set_with_dataframe(worksheet, dataframe)
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
        log.info("Command Received: user")
        if not can_execute(interaction.user, 2, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return
        await interaction.response.send_message(get_power(member))

    @tree.command (
        name="create_gang",
        description="Creates role, roster, and channels for a gang",
        guild=guild,
    )
    async def create_gang(interaction: Interaction, gang_name: str, color_request: str | None = None) -> None:
        """Creates all base resources for a gang including:
        - Discord Role
        - Roster
        - Discord Channels

        Parameters
        -----------
        gang_name: str
            the name of the gang to create
        color: str
            the primary color of the gang in hex format (e.g. #000000, 000000)
        """
        log.info("Command Received: create_gang")
        if not can_execute(interaction.user, 6, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return

        gang_name = string.capwords(gang_name.strip())

        worksheets = get_worksheets()
        if worksheets and gang_name in worksheets:
            await interaction.response.send_message("Gang already exists")
            return

        worksheet = create_worksheet(gang_name)
        if not worksheet:
            await interaction.response.send_message("Failed to create worksheet")
            return
        dataframe = pd.DataFrame(worksheet.get_values()[1:], columns=worksheet.get_values()[0])

        guild = await get_guild(client, guild_id)
        if not guild:
            await interaction.response.send_message("Failed to get guild")
            return
        
        newRole = await new_role(guild, gang_name, color_request)

        if not newRole:
            await interaction.response.send_message("Failed to create new role")
            return

        await interaction.response.send_message(f"```{dataframe}```\n@{newRole.name}")

    @tree.command(
        name="delete_gang",
        description="Deletes role, roster, and channels for a gang",
        guild=guild,
    )
    async def delete_gang(interaction: Interaction, gang_name: Role) -> None:
        """Deletes everything associated with a gang, primarily:
        - Discord Role
        - Roster
        - Discord Channels

        Parameters
        -----------
        gang_name: Role
            the role of the gang to delete
        """
        log.info("Command Received: delete_gang")
        if not can_execute(interaction.user, 6, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return

        worksheets = get_worksheets()
        if not worksheets or gang_name.name not in worksheets:
            await interaction.response.send_message("The provided role must be for a gang")
            return

        if not delete_worksheet(gang_name.name):
            await interaction.response.send_message("Failed to delete worksheet")
            return
        
        if not await delete_role(gang_name):
            await interaction.response.send_message("Failed to delete role")
            return
        
        await interaction.response.send_message("Gang deleted successfully")

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