import discord
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
    async def test(interaction: discord.Interaction, role: discord.Role) -> None:
        """Testing command

        Parameters
        -----------
        role: discord.Role
            testing parameter
        """
        try:
            log.info("Command Received: /test")

            # guild = interaction.guild
            # if not guild:
            #     raise Exception("Failed to get guild")

            if not sheets.can_execute(interaction.user, 4, role): # type: ignore
                await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
                return

            # newMap = {
            # "Gang Leader": "gl",
            # "High Command": "hc",
            # "Member": "m",
            # "Hangaround": "h"
            # }

            # newMap = await utility.create_subroles(guild, role, newMap)
            # print(newMap)



            await interaction.response.send_message("test done", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("Command failed", ephemeral=True)
            raise e

    create_com = discord.app_commands.Group(name="create", description="Creation commands")
    @create_com.command (
        name="gang",
        description="Creates a gang",
    )
    async def create_gang(interaction: discord.Interaction) -> None:
        """Creates all base resources for a gang including:
        - Discord Roles
        - Discord Category & Channels
        - Roster
        """
        try:
            log.info("Command Received: /create gang")

            if not sheets.can_execute(interaction.user, 5, None): # type: ignore
                await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
                return

            await interaction.response.send_modal(CreateGangForm())

        except Exception as e:
            await interaction.followup.send("Command failed", ephemeral=True)
            raise e
    tree.add_command(create_com, guild=guild)

    delete_com = discord.app_commands.Group(name="delete", description="Deletion commands")
    @delete_com.command (
        name="data",
        description="Delete Gang Bot's entire database",
    )
    async def delete_data(interaction: discord.Interaction) -> None:
        try:
            log.info("Command Received: /data delete")

            if not sheets.can_execute(interaction.user, 5): # type: ignore
                await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)

            async def confirm_callback(interaction: discord.Interaction):
                sheets.reset_spreadsheet()
                worksheet = sheets.get_worksheet("bot_data")
                values = worksheet.get_values()
                dataframe = pd.DataFrame(values[1:], columns=values[0])
                embed = discord.Embed(title="Data Deleted", description=dataframe.to_string())
                # await interaction.followup.send(f"```{dataframe.to_string()}```")
                await interaction.response.edit_message(embed=embed, view=discord.ui.View())

            async def cancel_callback(interaction: discord.Interaction):
                embed = discord.Embed(title="Cancelled", color=discord.Colour(16711680))
                await interaction.response.edit_message(embed=embed, view=discord.ui.View())

            embed = discord.Embed(title="Confirm Deletion", description="**Are you sure you want to delete all data?**", color=discord.Colour(16711680))
            embed.add_field(name="This is a destructive action and cannot be reversed!", value="", inline=False)

            confirm = discord.ui.Button(style=discord.ButtonStyle.red, label="Delete")
            confirm.callback = confirm_callback #type: ignore
            cancel = discord.ui.Button(style=discord.ButtonStyle.grey, label="Cancel")
            cancel.callback = cancel_callback

            view = discord.ui.View()
            view.add_item(confirm)
            view.add_item(cancel)

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            await interaction.followup.send("Command failed", ephemeral=True)
            raise e

    @delete_com.command(
        name="gang",
        description="Deletes role, roster, and channels for a gang",
    )
    async def delete_gang(interaction: discord.Interaction, role: discord.Role) -> None:
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
            await interaction.response.defer(ephemeral=True)

            if not sheets.can_execute(interaction.user, 5, role): # type: ignore
                await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
                return

            sheetnames = [ws.title for ws in sheets.get_worksheets()]
            if not sheetnames or role.name not in sheetnames:
                await interaction.followup.send("The provided role must be for a gang", ephemeral=True)
                return

            # Delete category
            cid = sheets.get_category_id(role)
            guild = interaction.guild
            guild = interaction.guild
            if not guild: raise Exception("Could not get guild")
            await utility.delete_category(guild, cid)

            # Delete worksheet
            sheets.delete_worksheet(role.name, role)
            await role.delete()

            # Delete roles

            await interaction.followup.send("Gang deleted successfully", ephemeral=True)

        except Exception as e:
            await interaction.followup.send("Command failed", ephemeral=True)
            raise e
    tree.add_command(delete_com, guild=guild)

    data_com = discord.app_commands.Group(name="data", description="...")
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
            await interaction.response.defer(ephemeral=True)

            if not sheets.can_execute(interaction.user, 2, None): # type: ignore
                await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
                return

            bot_data = sheets.get_worksheet("bot_data")
            cid = sheets.get_category_id(role)
            guild = interaction.guild
            if not guild: raise Exception("Could not get guild")

            dataframe = sheets.get_as_dataframe(sheets.update_data_worksheet(
                role=role,
                category=utility.get_category(guild, cid)))

            await interaction.followup.send(f"```{dataframe.to_string()}```", ephemeral=True)

        except Exception as e:
            await interaction.followup.send("Command failed", ephemeral=True)
            raise e

    @data_com.command (
        name="gang",
        description="get gang sheet"
    )
    async def data_gang(interaction: discord.Interaction, role: discord.Role) -> None:
        dataframe = sheets.get_as_dataframe(sheets.get_worksheet(role.name))
        await interaction.response.send_message(f"```{dataframe.to_string()}```", ephemeral=True)

    @data_com.command (
        name="bot",
        description="get bot sheet"
    )
    async def data_bot(interaction: discord.Interaction) -> None:
        dataframe = sheets.get_as_dataframe(sheets.get_worksheet('bot_data'))
        await interaction.response.send_message(f"```{dataframe.to_string()}```", ephemeral=True)
    tree.add_command(data_com, guild=guild)

class CreateGangForm(discord.ui.Modal, title="Create Gang"):
    name = discord.ui.TextInput(
        label="What is the name of your gang?",
        placeholder="Cool Gang Name",
        custom_id="name",
        style=discord.TextStyle.short,
        max_length=16,
        row=0,
        required=True
    )
    gl_name = discord.ui.TextInput(
        label="What do you call your Gang Leader?",
        placeholder="Gang Leader",
        custom_id="gl_name",
        default="Gang Leader",
        style=discord.TextStyle.short,
        max_length=16,
        row=1
    )
    hc_name = discord.ui.TextInput(
        label="What do you call your High Command?",
        placeholder="High Command",
        custom_id="hc_name",
        default="High Command",
        style=discord.TextStyle.short,
        max_length=16,
        row=2
    )
    m_name = discord.ui.TextInput(
        label="What do you call a Member?",
        placeholder="Member",
        custom_id="m_name",
        default="Member",
        style=discord.TextStyle.short,
        max_length=16,
        row=3
    )
    ha_name = discord.ui.TextInput(
        label="What do you call a Hangaround?",
        placeholder="Hangaround",
        custom_id="ha_name",
        default="Hangaround",
        style=discord.TextStyle.short,
        max_length=16,
        row=4
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild: raise Exception("Could not get guild")

        gang_name = string.capwords(str(self.name).strip())
        all_gangs = [role.name for role in guild.roles]
        if gang_name in all_gangs:
            await interaction.followup.send(f"A gang named {gang_name} already exists")
            return

        sheets.create_worksheet(gang_name)
        newRole = await utility.new_role(guild, gang_name)
        newMap = {
            "Gang Leader": string.capwords(str(self.gl_name).strip()),
            "High Command": string.capwords(str(self.hc_name).strip()),
            "Member": string.capwords(str(self.m_name).strip()),
            "Hangaround": string.capwords(str(self.ha_name).strip())
            }
        newMap = await utility.create_subroles(guild, newRole, newMap)
        newCategory = await utility.new_category(guild, newRole)

        dataframe = sheets.get_as_dataframe(sheets.update_data_worksheet(newRole, newMap, newCategory))
        await interaction.followup.send(f"```{dataframe}```\n{newRole.mention} - {newCategory.mention}", ephemeral=True)