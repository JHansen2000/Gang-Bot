import discord
import gspread
import discord.utils
import sheets
import utility
import string
import pandas as pd

import logger
log = logger.Logger()

def get_commands(tree: discord.app_commands.CommandTree[discord.Client], guild: discord.Object):
    @tree.command (
        name="test",
        description="refresh sheets db and return new sheet",
        guild=guild,
    )
    async def test(interaction: discord.Interaction, name: str) -> None:
        """Testing command

        Parameters
        -----------
        name: str
            testing parameter
        """
        try:
            log.info("Command Received: /test")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 2, None): # type: ignore
                await interaction.followup.send("You do not have permission to use this command")
                return

            await interaction.response.send_modal(CreateGang())

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e

    pingpong = discord.app_commands.Group(name="ping", description="...")
    @pingpong.command (
        name="ping",
        description="Ping Gang Bot!",
    )
    async def ping(interaction: discord.Interaction) -> None:
        try:
            log.info("Command Received: /ping ping")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 1, None): # type: ignore
                await interaction.followup.send("You do not have permission to use this command")
                return
            await interaction.followup.send("Pong!")

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e

    @pingpong.command (
        name="pong",
        description="Ping Gang Bot!",
    )
    async def pong(interaction: discord.Interaction) -> None:
        try:
            log.info("Command Received: /ping pong")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 1, None): # type: ignore
                await interaction.followup.send("You do not have permission to use this command")
                return
            await interaction.followup.send("Ping!")

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e
    tree.add_command(pingpong, guild=guild)

    data_com = discord.app_commands.Group(name="data", description="...")
    @data_com.command (
        name="delete",
        description="Delete Gang Bot's entire database",
    )
    async def data_delete(interaction: discord.Interaction) -> None:
        try:
            log.info("Command Received: /data delete")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 5, None): # type: ignore
                await interaction.followup.send("You do not have permission to use this command")
                return

            sheets.reset_spreadsheet()
            worksheet = sheets.get_worksheet("bot_data")
            values = worksheet.get_values()
            dataframe = pd.DataFrame(values[1:], columns=values[0])
            await interaction.followup.send(f"```{dataframe.to_string()}```")

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e

    @data_com.command (
        name="refresh",
        description="refresh sheets db and return new sheet",
    )
    async def data_refresh(interaction: discord.Interaction, role: discord.Role) -> None:
        """Refresh the gang database to pick up any new changes

        Parameters
        -----------
        role: discord.Role
            testing parameter
        category: discord.ChannelCategory
            testing parameter
        """
        try:
            log.info("Command Received: /data refresh")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 2, None): # type: ignore
                await interaction.response.send_message("You do not have permission to use this command")
                return

            bot_data = sheets.get_worksheet("bot_data")
            cid = sheets.get_category_id(role)
            guild = interaction.guild
            if not guild: raise Exception("Could not get guild")

            dataframe = sheets.get_as_dataframe(sheets.update_data_worksheet(
                role=role,
                category=utility.get_category(guild, cid)))

            await interaction.followup.send(f"```{dataframe.to_string()}```")

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e

    @data_com.command (
        name="gang",
        description="get gang sheet"
    )
    async def data_gang(interaction: discord.Interaction, role: discord.Role) -> None:
        dataframe = sheets.get_as_dataframe(sheets.get_worksheet(role.name))
        await interaction.response.send_message(f"```{dataframe.to_string()}```")

    @data_com.command (
        name="bot",
        description="get bot sheet"
    )
    async def data_bot(interaction: discord.Interaction) -> None:
        dataframe = sheets.get_as_dataframe(sheets.get_worksheet('bot_data'))
        await interaction.response.send_message(f"```{dataframe.to_string()}```")
    tree.add_command(data_com, guild=guild)

    gang_com = discord.app_commands.Group(name="gang", description="...")
    @gang_com.command (
        name="create",
        description="Creates role, roster, and channels for a gang",
    )
    async def gang_create(interaction: discord.Interaction, gang_name: str, color_request: str | None = None) -> None:
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
        try:
            log.info("Command Received: /gang create")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 5, None): # type: ignore
                await interaction.followup.send("You do not have permission to use this command")
                return

            gang_name = string.capwords(gang_name.strip())
            guild = interaction.guild
            if not guild: raise Exception("Could not get guild")



            all_gangs = [role.name for role in guild.roles]
            if gang_name in all_gangs:
                await interaction.followup.send(f"A gang named {gang_name} already exists")
                return

            newRole = await utility.new_role(guild, gang_name, color_request)
            newCategory = await utility.new_category(guild, newRole)
            sheets.create_worksheet(gang_name) # Returns worksheet
            dataframe = sheets.get_as_dataframe(sheets.update_data_worksheet(newRole, newCategory))
            await interaction.followup.send(f"```{dataframe}```\n{newRole.mention} - {newCategory.mention}")

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e

    @gang_com.command(
        name="delete",
        description="Deletes role, roster, and channels for a gang",
    )
    async def gang_delete(interaction: discord.Interaction, role: discord.Role) -> None:
        """Deletes everything associated with a gang, primarily:
        - Discord Role
        - Roster
        - Discord Channels

        Parameters
        -----------
        gang_role: Role
            the role of the gang to delete
        """
        try:
            log.info("Command Received: /gang delete")
            await interaction.response.defer()

            if not utility.can_execute(interaction.user, 5, None): # type: ignore
                await interaction.followup.send("You do not have permission to use this command")
                return

            sheetnames = [ws.title for ws in sheets.get_worksheets()]
            if not sheetnames or role.name not in sheetnames:
                await interaction.followup.send("The provided role must be for a gang")
                return

            # Delete category
            cid = sheets.get_category_id(role)
            guild = interaction.guild
            guild = interaction.guild
            if not guild: raise Exception("Could not get guild")
            await utility.delete_category(guild, cid)

            sheets.delete_worksheet(role.name, role)
            await role.delete()
            await interaction.followup.send("Gang deleted successfully")

        except Exception as e:
            await interaction.followup.send("Command failed")
            raise e

        # try:
        #     log.info("Command Received: ")
        #     await interaction.response.defer()

        # except Exception as e:
        #     await interaction.followup.send("Command failed")
        #     raise e
    tree.add_command(gang_com, guild=guild)

class CreateGang(discord.ui.Modal, title="Create Gang"):
    gl_name = discord.ui.TextInput(
        label="What do you call your Gang Leader?",
        placeholder="Gang Leader"
    )
    hc_name = discord.ui.TextInput(
        label="What do you call your High Command?",
        placeholder="High Command"
    )
    m_name = discord.ui.TextInput(
        label="What do you call a Member?",
        placeholder="Member"
    )
    ha_name = discord.ui.TextInput(
        label="What do you call a Hangaround?",
        placeholder="Hangaround"
    )

    # name = discord.ui.TextInput(
    #     label='Name',
    #     placeholder='Your name here...',
    # )
    # feedback = discord.ui.TextInput(
    #     label='What do you think of this new feature?',
    #     style=discord.TextStyle.long,
    #     placeholder='Type your feedback here...',
    #     required=False,
    #     max_length=300,
    # )