import discord
import string
import utility
import sheets
import re
from logger import Logger
log = Logger()

dne_embed = discord.Embed(title="No Gangs Exist", description="**You can create one with** `/gang create`", color=discord.Colour.red())
fail_embed = discord.Embed(title="Command Failed", description="Something went wrong, ask a Developer for help!", color=discord.Colour.red())
permission_embed = discord.Embed(title="Insufficient Permissions", description="You do not have permission to run this command!", color=discord.Colour.dark_red())

def get_commands(tree: discord.app_commands.CommandTree[discord.Client],
                 db: sheets.Database,
                 guild: discord.Object | None = None):

  @tree.command (
    name="test",
    description="test command",
    guild=guild
  )
  async def test(interaction: discord.Interaction, gang: str) -> None:
    """Test Command

    Parameters
    -----------
    gang_role: Role
      the role of the gang to print
    """
    try:
      log.info("Command Received: /test")
      await interaction.response.defer(ephemeral=True)

      if gang == "":
        await interaction.followup.send(embed=dne_embed, view=discord.ui.View(), ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")
      role = sheets.get_role(guild, gang)

      if not db.can_execute(interaction.user, 4, role): # type: ignore
        await interaction.followup.send(embed=permission_embed, ephemeral=True)
        return
      await interaction.followup.send("Done", ephemeral=True)

    except Exception as e:
      await interaction.followup.send(embed=fail_embed, ephemeral=True)
      raise e
  @test.autocomplete("gang")
  async def test_autocomplete(interaction: discord.Interaction, gang: str) -> list[discord.app_commands.Choice[str]]:
    return db.get_gang_choices(interaction.guild)

  create_com = discord.app_commands.Group(name="create", description="Creation commands")
  @create_com.command (
    name="gang",
    description="Creates a gang"
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
        await interaction.response.send_message(embed=permission_embed, ephemeral=True)
        return

      await interaction.response.send_modal(CreateGangForm(db))

    except Exception as e:
      await interaction.followup.send(embed=fail_embed, ephemeral=True)
      raise e
  tree.add_command(create_com, guild=guild)

  delete_com = discord.app_commands.Group(name="delete", description="Deletion commands")
  @delete_com.command(
    name="gang",
    description="Deletes role, roster, and channels for a gang"
  )
  async def delete_gang(interaction: discord.Interaction, gang: str) -> None:
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

      if gang == "":
        await interaction.followup.send(embed=dne_embed, view=discord.ui.View(), ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")
      role = sheets.get_role(guild, gang)

      if not db.can_execute(interaction.user, 5, role): # type: ignore
        await interaction.followup.send(embed=permission_embed, ephemeral=True)
        return

      if role.name not in db.sheetnames:
        await interaction.followup.send("The provided role must be for a gang", ephemeral=True)
        return

      # Delete category
      cid = db.get_cid(role)
      await utility.delete_category(guild, cid)

      # Delete subroles
      for subrole in db.get_subroles(role, guild):
        await subrole.delete()

      # Delete worksheet
      db.delete_sheet(role.name, role)

      # Delete primary role
      name = role.name
      await role.delete()

      await interaction.followup.send(embed=discord.Embed(title="Gang Deleted", description=f"{name} was deleted successfully!", color=discord.Colour.dark_green()), ephemeral=True)

    except Exception as e:
      await interaction.followup.send(embed=fail_embed, ephemeral=True)
      raise e

  @delete_gang.autocomplete("gang")
  async def delete_autocomplete(interaction: discord.Interaction, gang: str) -> list[discord.app_commands.Choice[str]]:
    return db.get_gang_choices(interaction.guild)

  @delete_com.command (
    name="data",
    description="Delete Gang Bot's entire database"
  )
  async def delete_data(interaction: discord.Interaction) -> None:
    try:
      log.info("Command Received: /data delete")

      if not db.can_execute(interaction.user, 5, None): # type: ignore
        await interaction.response.send_message(embed=permission_embed, ephemeral=True)
        return

      await interaction.response.defer(ephemeral=True)

      async def confirm_callback(interaction: discord.Interaction):
        db.reset_data()
        embed = discord.Embed(title="Data Deleted", description=db.bot_df.to_string(), color=discord.Colour.dark_green())
        await interaction.response.edit_message(embed=embed, view=discord.ui.View())

      async def cancel_callback(interaction: discord.Interaction):
        embed = discord.Embed(title="Cancelled", color=discord.Colour.dark_green())
        await interaction.response.edit_message(embed=embed, view=discord.ui.View())

      embed = discord.Embed(title="Confirm Deletion", description="**Are you sure you want to delete all data?**", color=discord.Colour.red())
      embed.add_field(name="This is a destructive action and cannot be reversed!", value="", inline=False)

      confirm = discord.ui.Button(style=discord.ButtonStyle.red, label="Delete")
      confirm.callback = confirm_callback
      cancel = discord.ui.Button(style=discord.ButtonStyle.grey, label="Cancel")
      cancel.callback = cancel_callback

      view = discord.ui.View()
      view.add_item(confirm)
      view.add_item(cancel)
      await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    except Exception as e:
      await interaction.followup.send(embed=fail_embed, ephemeral=True)
      raise e
  tree.add_command(delete_com, guild=guild)

  refresh_com = discord.app_commands.Group(name="refresh", description="Refresh commands")
  @refresh_com.command(
    name="roster",
    description="Refresh a gang's roster from the database"
  )
  async def refresh_roster(interaction: discord.Interaction, gang: str) -> None:
    """Refreshses a gang's roster

    Parameters
    -----------
    gang_role: Role
        the role of the gang to refresh
    """
    try:
      log.info("Command Received: /refresh roster")
      await interaction.response.defer(ephemeral=True)

      if gang == "":
        await interaction.followup.send(embed=dne_embed, view=discord.ui.View(), ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")
      role = sheets.get_role(guild, gang)
      await db.refresh_roster(role)
      await interaction.followup.send(embed=discord.Embed(title=f"{role.name} Roster Refreshed", color=discord.Colour.green()))

    except Exception as e:
      await interaction.followup.send(embed=fail_embed, ephemeral=True)
      raise e

  @refresh_roster.autocomplete("gang")
  async def refresh_roster_autocomplete(interaction: discord.Interaction, gang: str) -> list[discord.app_commands.Choice[str]]:
    return db.get_gang_choices(interaction.guild)
  tree.add_command(refresh_com, guild=guild)

  change_com = discord.app_commands.Group(name="change", description="Change commands")
  @change_com.command(
    name="color",
    description="Change the color of a gang"
  )
  async def change_color(interaction: discord.Interaction, gang: str) -> None:
    """Changes the color of a gang's primary role

    Parameters
    -----------
    gang_role: Role
        the role of the gang to change
    """
    try:
      log.info("Command Received: /change color")
      await interaction.response.defer(ephemeral=True)

      if gang == "":
        await interaction.followup.send(embed=dne_embed, view=discord.ui.View(), ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")
      role = sheets.get_role(guild, gang)

      if not db.can_execute(interaction.user, 4, role): # type: ignore
        await interaction.followup.send(embed=permission_embed, ephemeral=True)
        return

      res = await color_embed(role, color=role.color)
      await interaction.followup.send(embed=res[0], view=res[1])

    except Exception as e:
      await interaction.followup.send(embed=fail_embed, ephemeral=True)
      raise e

  @change_color.autocomplete("gang")
  async def change_color_autocomplete(interaction: discord.Interaction, gang: str) -> list[discord.app_commands.Choice[str]]:
    return db.get_gang_choices(interaction.guild)

  @change_com.command(
    name="iban",
    description="Change or Set your IBAN"
  )
  async def change_iban(interaction: discord.Interaction, gang: str) -> None:
    try:
      log.info("Command Received: /change iban")

      if gang == "":
        await interaction.followup.send(embed=dne_embed, view=discord.ui.View(), ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")
      role = sheets.get_role(guild, gang)

      if not interaction.user in role.members: # type: ignore
        await interaction.response.send_message(embed=permission_embed, ephemeral=True)
        return

      await interaction.response.send_modal(sheets.ChangeIBANModal(role, db))

    except Exception as e:
      await interaction.response.send_message(embed=fail_embed, ephemeral=True)
      raise e

  @change_iban.autocomplete("gang")
  async def change_iban_autocomplete(interaction: discord.Interaction, gang: str) -> list[discord.app_commands.Choice[str]]:
    return db.get_gang_choices(interaction.guild)

  @change_com.command(
    name="subroles",
    description="Change the names of your gang subroles"
  )
  async def change_subroles(interaction: discord.Interaction, gang: str) -> None:
    try:
      log.info("Command Received: /change subroles")

      if gang == "":
        await interaction.followup.send(embed=dne_embed, view=discord.ui.View(), ephemeral=True)
        return

      guild = interaction.guild
      if not guild: raise Exception("Could not get guild")
      role = sheets.get_role(guild, gang)

      if not db.can_execute(interaction.user, 4, role): # type: ignore
        await interaction.followup.send(embed=permission_embed, ephemeral=True)
        return

      await interaction.response.send_modal(sheets.ChangeSubrolesModal(role, db))

    except Exception as e:
      await interaction.response.send_message(embed=fail_embed, ephemeral=True)
      raise e

  @change_subroles.autocomplete("gang")
  async def change_subroles_autocomplete(interaction: discord.Interaction, gang: str) -> list[discord.app_commands.Choice[str]]:
    return db.get_gang_choices(interaction.guild)
  tree.add_command(change_com, guild=guild)

class CreateGangForm(discord.ui.Modal):
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
    newRole = await self.db.create_role(guild, gang_name)
    newMap = {
      string.capwords(str(self.gl_name).strip()): 4,
      string.capwords(str(self.hc_name).strip()): 3,
      string.capwords(str(self.m_name).strip()): 2,
      string.capwords(str(self.ha_name).strip()): 1
      }
    newMap = await self.db.create_subroles(guild, newRole, newMap)
    unpruned = [guild.get_role(int(rid)) for rid in newMap.keys()]
    subroles = [sr for sr in unpruned if sr is not None]
    newCategory = await utility.create_category(guild, newRole)
    await utility.update_gang_category(newCategory, subroles)

    channels = await utility.create_gang_channels(guild, newRole, subroles, newCategory)
    roster = channels[0]
    radio = channels[1]

    self.db.update_bot(newRole, newMap, roster.id, radio.id, category=newCategory)
    res = await color_embed(newRole, roster)
    await interaction.followup.send(embed=res[0], view=res[1])

    await self.db.update_roster(roster, newRole)

    res = await radio_embed(newRole, self.db, radio)
    await self.db.update_radio_message(radio, newRole)

async def color_embed(gang: discord.Role, roster: discord.TextChannel | None = None, color: discord.Colour = discord.Colour.lighter_grey()) -> tuple[discord.Embed, discord.ui.View]:
  description = f"< This is the current gang color ({'#%02x%02x%02x' % color.to_rgb()}). Is this correct?"
  embed = discord.Embed(title=f"Pick a color for {gang.name}", description=description, color=color)
  embed.add_field(name=f"You can change this later with `/change color {gang.name}`", value="", inline=False)

  async def confirm_color(interaction: discord.Interaction) -> None:
    await gang.edit(color = color)
    if roster:
      com_type = "Created"
    else:
      com_type = "Configured"
    description = gang.mention + f" was {com_type.lower()} successfully"
    if roster:
      description += '\n' + roster.mention
    await interaction.response.edit_message(embed=discord.Embed(title=f"Gang {com_type}", description=description, color=color), view=discord.ui.View())

  async def change_color(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(ChooseColorModal(gang, roster, color))

  confirm = discord.ui.Button(style=discord.ButtonStyle.green, label="Confirm Color")
  confirm.callback = confirm_color
  change = discord.ui.Button(style=discord.ButtonStyle.blurple, label="Change Color")
  change.callback = change_color

  view = discord.ui.View()
  view.add_item(confirm)
  view.add_item(change)

  return embed, view

async def radio_embed(gang: discord.Role, db: sheets.Database, radio: discord.TextChannel, embed: discord.Embed | None = None) -> tuple[discord.Embed, discord.ui.View]:
  if not embed:
    embed = discord.Embed(title=f"Set Up Radio - {gang.name}", description="Set up radio channels now or later?", color=gang.color)


    async def set_now(interaction: discord.Interaction) -> None:
      radio_embed = await interaction.response.send_modal(sheets.ChangeRadioModal(gang, db, True))
      if not radio_embed:
        await interaction.response.edit_message(embed=discord.Embed(title="Something Went Wrong", description=f"Could not set radio channels!\nTry again with `/change radio` OR press the button in {radio.mention}"), view=discord.ui.View())
      

    async def set_later(interaction: discord.Interaction) -> None:
      newEmbed = discord.Embed(title=f"Radio Channels - {gang.name}", description="Not set!\nSet with `/change radio` OR press the button below!", color=gang.color)

    button_1 = discord.ui.Button(style=discord.ButtonStyle.green, label="Set Now")
    button_1.callback = set_now
    button_2 = discord.ui.Button(style=discord.ButtonStyle.gray, label="Later")
    button_2.callback = set_later

  else:
    async def confirm_callback(interaction: discord.Interaction) -> None:
      temp = 1

    async def change_callback(interaction: discord.Interaction) -> None:
      temp = 1

    button_1 = discord.ui.Button(style=discord.ButtonStyle.green, label="Set Now")
    button_1.callback = confirm_callback
    button_2 = discord.ui.Button(style=discord.ButtonStyle.gray, label="Later")
    button_2.callback = change_callback

  view = discord.ui.View()
  view.add_item(button_1)
  view.add_item(button_2)



class ChooseColorModal(discord.ui.Modal):
  def __init__(self, gang: discord.Role, roster: discord.TextChannel | None, color: discord.Colour = discord.Colour.greyple()):
    self.gang: discord.Role = gang
    self.color: discord.Colour = color
    self.roster: discord.TextChannel | None = roster
    super().__init__(title=f"Set Color for {gang.name}")

  hex = discord.ui.TextInput(
    label="Enter your color hex",
    placeholder="#123abc",
    max_length = 7,
    min_length = 6,
    required=True,
    row = 0
  )

  async def on_submit(self, interaction: discord.Interaction) -> None:
    flag = False

    regex = re.search(pattern="#?[a-fA-F0-9]{6}", string=str(self.hex))
    if not regex:
      flag = True
    else:
      hex = str(self.hex) if str(self.hex)[0] != '#' else str(self.hex)[1:]
      col_int = int(hex, 16)
      if col_int < 0 or  col_int > 16777215:
        flag = True

    if flag:
      res = await color_embed(self.gang)
      await interaction.response.edit_message(embed=discord.Embed(title="Improperly Formatted Color", description="The value you entered is not a valid hex color, please try again", color=self.gang.color), view=res[1])
      return

    color = discord.Colour(col_int)
    res = await color_embed(self.gang, self.roster, color)
    await interaction.response.edit_message(embed=res[0], view=res[1])


