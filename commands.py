from code import interact
from discord import CategoryChannel, Interaction, Member, Role, Client, Object, app_commands
import discord.utils
import sheets
import utility
import string
import pandas as pd
import logger
log = logger.Logger()

def get_commands(tree: app_commands.CommandTree[Client], guild: Object):

    @tree.command (
        name="test",
        description="refresh sheets db and return new sheet",
        guild=guild,
    )
    async def test(interaction: Interaction, role: Role) -> None:
        """Testing command

        Parameters
        -----------
        role: discord.Role
            testing parameter
        """
        log.info("Command Received: test")

        if not utility.can_execute(interaction.user, 2, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("failed")
            return

        res = sheets.get_category_id(role)

        await interaction.response.send_message(res)

    @tree.command (
        name="ping",
        description="Ping Gang Bot!",
        guild=guild,
    )
    async def ping(interaction: Interaction) -> None:
        log.info("Command Received: ping")

        if not utility.can_execute(interaction.user, 1, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return
        await interaction.response.send_message("Pong!")

    @tree.command (
        name="delete_data",
        description="Delete Gang Bot's entire database",
        guild=guild,
    )
    async def delete_data(interaction: Interaction) -> None:
        log.info("Command Received: delete_data")
        await interaction.response.defer()

        if not utility.can_execute(interaction.user, 5, None): # type: ignore
            await interaction.followup.send("You do not have permission to use this command")
            return

        if sheets.reset_spreadsheet():
            worksheet = sheets.get_worksheet("bot_data")
            if not worksheet:
                await interaction.response.send_message(f"Could not find bot_data sheet")
                return

            values = worksheet.get_values()
            dataframe = pd.DataFrame(values[1:], columns=values[0])
            await interaction.followup.send(f"```{dataframe.to_string()}```")
        else:
            await interaction.followup.send("Failed to delete database")

    @tree.command (
        name="refresh_sheet",
        description="refresh sheets db and return new sheet",
        guild=guild,
    )
    async def refresh_sheet(interaction: Interaction, role: Role, category: CategoryChannel) -> None:
        """Testing command

        Parameters
        -----------
        role: discord.Role
            testing parameter
        category: discord.ChannelCategory
            testing parameter
        """
        log.info("Command Received: refresh_sheet")

        if not utility.can_execute(interaction.user, 2, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return

        worksheet = sheets.get_worksheet("bot_data")
        if not worksheet:
            await interaction.response.send_message(f"Could not find bot_data sheet")
            return

        worksheet = sheets.update_worksheet(worksheet, role=role, category=category)
        if not worksheet:
            await interaction.response.send_message("failed")
            return

        values = worksheet.get_values()
        dataframe = pd.DataFrame(values[1:], columns=values[0])

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

        if not utility.can_execute(interaction.user, 2, None): # type: ignore
            await interaction.response.send_message("You do not have permission to use this command")
            return
        await interaction.response.send_message(utility.get_power(member))

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
        await interaction.response.defer()

        if not utility.can_execute(interaction.user, 5, None): # type: ignore
            await interaction.followup.send("You do not have permission to use this command")
            return

        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Failed to get guild")
            return

        gang_name = string.capwords(gang_name.strip())
        all_gangs = [role.name for role in guild.roles]
        if gang_name in all_gangs:
            await interaction.followup.send(f"A gang named {gang_name} already exists")
            return

        newRole = await utility.new_role(guild, gang_name, color_request)
        if not newRole:
            await interaction.followup.send("Failed to create new role")
            return
        newCategory = await utility.new_category(guild, newRole)
        if not newCategory:
            await interaction.followup.send("Failed to create category")
            return
        newWorksheet = sheets.create_worksheet(gang_name)
        if not newWorksheet:
            await interaction.followup.send("Failed to create worksheet")
            return

        bot_data = sheets.get_worksheet('bot_data')
        if not bot_data:
            await interaction.followup.send("Failed to get bot_data")
            return
        worksheet = sheets.update_worksheet(bot_data, role=newRole, category=newCategory)

        dataframe = pd.DataFrame(worksheet.get_values()[1:], columns=worksheet.get_values()[0])
        await interaction.followup.send(f"```{dataframe}```\n{newRole.mention} - {newCategory.mention}")

    @tree.command(
        name="delete_gang",
        description="Deletes role, roster, and channels for a gang",
        guild=guild,
    )
    async def delete_gang(interaction: Interaction, role: Role) -> None:
        """Deletes everything associated with a gang, primarily:
        - Discord Role
        - Roster
        - Discord Channels

        Parameters
        -----------
        gang_role: Role
            the role of the gang to delete
        """
        log.info("Command Received: delete_gang")
        await interaction.response.defer()

        if not utility.can_execute(interaction.user, 5, None): # type: ignore
            await interaction.followup.send("You do not have permission to use this command")
            return

        worksheets = sheets.get_worksheets()
        # This should never be true
        if not worksheets:
            return

        sheetnames = [ws.title for ws in worksheets]
        if not sheetnames or role.name not in sheetnames:
            await interaction.followup.send("The provided role must be for a gang")
            return

        # Delete category
        cid = sheets.get_category_id(role)
        if not cid:
            await interaction.followup.send("Failed to get CID")
            return
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Failed to get guild")
            return
        if not await utility.delete_category(guild, cid):
            await interaction.followup.send("Failed to delete category")

        # Delete worksheet
        if not sheets.delete_worksheet(role.name, role):
            await interaction.followup.send("Failed to delete worksheet")
            return

        # Delete role
        if not await utility.delete_role(role):
            await interaction.followup.send("Failed to delete role")
            return

        await interaction.followup.send("Gang deleted successfully")

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