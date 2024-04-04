import discord
import string
from sheets import Database, get_as_dataframe
import utility
from logger import Logger
log = Logger()

def get_commands(tree: discord.app_commands.CommandTree[discord.Client],
                 db: Database,
                 guild: discord.Object | None = None):

  @tree.command (
    name="test",
    description="test command",
    guild=guild
  )
  async def test(interaction: discord.Interaction) -> None:
    db.reset_data()
    await interaction.response.send_message(f"{db.bot_df}", ephemeral=True)

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

      # if not sheets.can_execute(interaction.user, 5, None): # type: ignore
      #   await interaction.response.send_message("You do not have permission to use this command", ephemeral=True)
      #   return

      await interaction.response.send_modal(CreateGangForm(db))

    except Exception as e:
      await interaction.followup.send("Command failed", ephemeral=True)
      raise e
  tree.add_command(create_com, guild=guild)


class CreateGangForm(discord.ui.Modal, title="Create Gang"):

  def __init__(self, db: Database):
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
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    if not guild: raise Exception("Could not get guild")

    gang_name = string.capwords(str(self.name).strip())
    if gang_name in self.db.sheetnames:
      await interaction.followup.send(f"A gang named {gang_name} already exists")
      return

    self.db.create_sheet(gang_name)
    newRole = await self.db.create_role(guild, gang_name)
    newMap = {
      "Gang Leader": string.capwords(str(self.gl_name).strip()),
      "High Command": string.capwords(str(self.hc_name).strip()),
      "Member": string.capwords(str(self.m_name).strip()),
      "Hangaround": string.capwords(str(self.ha_name).strip())
      }
    newMap = await self.db.create_subroles(guild, newRole, newMap)
    newCategory = await self.db.create_category(guild, newRole)

    dataframe = get_as_dataframe(self.db.update_bot(newRole, newMap, newCategory))
    await interaction.followup.send(f"```{dataframe}```\n{newRole.mention} - {newCategory.mention}", ephemeral=True)