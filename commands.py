import discord
import string
import utility
import sheets
import pandas as pd
from logger import Logger
log = Logger()

def get_commands(tree: discord.app_commands.CommandTree[discord.Client],
                 db: sheets.Database,
                 guild: discord.Object | None = None):
  if len(db.sheetnames) < 1: # Move this functionality into a db var
    role_choices=[discord.app_commands.Choice(name="No gangs exist", value="")]
  else:
    role_choices=[discord.app_commands.Choice(name=sheets.get_df_at(db.bot_df, int(rid), "RID", "Name"), value=rid) for rid in db.get_all_RIDs()]

  @tree.command (
    name="reset",
    description="reset all data",
    guild=guild
  )
  async def reset(interaction: discord.Interaction) -> None:
    db.reset_data()
    await interaction.response.send_message(f"{db.bot_df}", ephemeral=True)

  @tree.command (
    name="test",
    description="test command",
    guild=guild
  )
  @discord.app_commands.choices(gang=role_choices)
  async def test(interaction: discord.Interaction, gang: discord.app_commands.Choice[str]) -> None:
    """Test Command

    Parameters
    -----------
    gang_role: Role
      the role of the gang to print
    """
    try:
      if gang.value == "":
          embed = discord.Embed(title="No Gangs Exist", description="**You can create one with** `/gang create`", color=discord.Colour(16711680))
          await interaction.response.send_message(embed=embed, view=discord.ui.View(), ephemeral=True)
          return

      await interaction.response.defer(ephemeral=True)
      await interaction.followup.send(f"{db.bot_df.to_string(index=False)}", ephemeral=True)
      await interaction.followup.send(f"{db.get_gang_df(gang.name).to_string(index=False)}", ephemeral=True)

    except Exception as e:
      await interaction.followup.send(f"Command failed", ephemeral=True)
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

      if not db.can_execute(interaction.user, 5, None): # type: ignore
        await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
        return

      await interaction.response.send_modal(CreateGangForm(db))

    except Exception as e:
      await interaction.followup.send("Command failed", ephemeral=True)
      raise e
  tree.add_command(create_com, guild=guild)

  delete_com = discord.app_commands.Group(name="delete", description="Deletion commands")
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

      if not db.can_execute(interaction.user, 5, role): # type: ignore
        await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
        return

      if role.name not in db.sheetnames:
        await interaction.followup.send("The provided role must be for a gang", ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")

      # Delete category
      cid = db.get_cid(role)
      await utility.delete_category(guild, cid)

      # Delete subroles
      for subrole in db.get_subroles(role, guild):
        await subrole.delete()

      # Delete worksheet
      db.delete_sheet(role.name, role)

      # Delete primary role
      await role.delete()

      await interaction.followup.send("Gang deleted successfully", ephemeral=True)

    except Exception as e:
      await interaction.followup.send("Command failed", ephemeral=True)
      raise e

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
        db.reset_data()
        embed = discord.Embed(title="Data Deleted", description=db.bot_df.to_string())
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
  tree.add_command(delete_com, guild=guild)

class CreateGangForm(discord.ui.Modal, title="Create Gang"):
  def __init__(self, db: sheets.Database):
    self.db = db
    super().__init__(title="Create Gang")

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
    await interaction.response.defer(thinking=True, ephemeral=True)

    guild = interaction.guild
    if not guild: raise Exception("Could not get guild")

    gang_name = string.capwords(str(self.name).strip())
    if gang_name in self.db.sheetnames:
      await interaction.followup.send(f"A gang named {gang_name} already exists")
      return

    self.db.create_sheet(gang_name)
    newRole = await utility.create_role(guild, gang_name)
    newMap = {
      string.capwords(str(self.gl_name).strip()): 4,
      string.capwords(str(self.hc_name).strip()): 3,
      string.capwords(str(self.m_name).strip()): 2,
      string.capwords(str(self.ha_name).strip()): 1
      }
    newMap = await utility.create_subroles(guild, newRole, newMap)
    newCategory = await utility.create_category(guild, newRole)

    dataframe = self.db.update_bot(newRole, newMap, newCategory)
    self.db.print_vars()
    await interaction.followup.send(f"```{dataframe}```\n{newRole.mention} - {newCategory.mention}", ephemeral=True)