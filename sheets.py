import os
import re
from discord import TextChannel
from dotenv import load_dotenv
import discord
from gspread import Spreadsheet, Worksheet, service_account
from gspread_dataframe import set_with_dataframe
from utility import get_role
from table2ascii import Alignment, table2ascii as t2a, PresetStyle
import pandas as pd
from datetime import date
from logger import Logger
log = Logger()

BOT_DATA_HEADERS = ["Name", "RID", "CID", "RoCID", "RaCID", "MIDs", "CRIDs", "Created", "Modified"]
GANG_DATA_HEADERS = ["ID", "Name", "Rank", "RID", "IBAN"]

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID: raise Exception("Unable to get ADMIN_ID")
BOT_ID = os.getenv("BOT_ID")
if not BOT_ID: raise Exception("Unable to get BOT_ID")

permission_embed = discord.Embed(title="Insufficient Permissions", description="You do not have permission to run this command!", color=discord.Colour.dark_red())

def connect_to_db(SPREADSHEET_ID: str) -> Spreadsheet:
  log.info(f"Connecting to database - {SPREADSHEET_ID}")
  spreadsheet = service_account(filename="private/private_key.json").open_by_key(SPREADSHEET_ID)
  worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
  log.info(f"Found worksheets - {worksheet_titles}")

  if "bot_data" not in worksheet_titles:
    log.warning("bot_data sheet not found - creating...")
    bot_data = spreadsheet.add_worksheet(
      title="bot_data",
      rows=1,
      cols=len(BOT_DATA_HEADERS),
      index=len(worksheet_titles))
    dataframe = pd.DataFrame(columns=BOT_DATA_HEADERS)
    set_with_dataframe(bot_data, dataframe, resize=True)
    log.info("bot_data sheet created")
  return spreadsheet

def isAdmin(member: discord.Member)-> bool:
    admin_role = get_role(member.guild, ADMIN_ID)
    return True if admin_role in member.roles else False

def get_as_dataframe(worksheet: Worksheet) -> pd.DataFrame:
  values = worksheet.get_values()
  dataframe = pd.DataFrame(values[1:], columns=values[0])
  return dataframe

def get_df_at(input: pd.DataFrame,
              id: int | str,
              key: str,
              value: str,
              read_dict: bool = False):
  retArray = input.loc[input[key] == str(id), value].array
  if len(retArray) < 1: raise Exception(f"Could not get df value ({id, key, value, read_dict}) ")
  retVal = retArray[0]
  return eval(retVal) if read_dict else retVal

def get_df_row(input: pd.DataFrame, id: int, key: str) -> list[str]:
  return input.index[input[key] == str(id)].tolist()

class Database:
  def __init__(self, SPREADSHEET_ID: str):
    self.SPREADSHEET_ID = SPREADSHEET_ID
    self.spreadsheet = connect_to_db(SPREADSHEET_ID)
    self.worksheets = self.spreadsheet.worksheets()

    self.sheetnames = [ws.title for ws in self.worksheets]
    self.sheetids = [ws.id for ws in self.worksheets]

    bot_index = self.get_worksheet_index('bot_data')
    self.bot_sheet = self.worksheets.pop(bot_index)
    self.bot_df = get_as_dataframe(self.bot_sheet)
    self.sheetnames.pop(bot_index)
    self.sheetids.pop(bot_index)

    log.info("Database initialized")

  async def init_gang_rosters(self, guild: discord.Guild):
    for gang in self.get_all_gangs(guild):
      channel_id = int(get_df_at(self.bot_df, gang.id, "RID", "RoCID"))
      roster = guild.get_channel(channel_id)
      if not roster: raise Exception(f"Could not get channel with ID {channel_id}")
      await self.refresh_roster(gang)

  def get_power(self,
                member: discord.Member,
                subroles: dict[str, int],
                opt_role: discord.Role | None = None,
                skipAdmin: bool = False) -> int:

    if not skipAdmin and isAdmin(member):
      log.info(f"@{member.name} is an admin")
      return 5

    power = 0
    member_roles = member.roles
    if opt_role:
        member_roles.append(opt_role)
    for role in member_roles:
        role_power = subroles.get(str(role.id))
        if role_power:
          power = max(role_power, power)
    log.info(f"@{member.name} has power {power}")
    return power

  def get_gang_choices(self, guild) -> list[discord.app_commands.Choice[str]]:
    if len(self.sheetnames) < 1:
      role_choices=[discord.app_commands.Choice(name="No gangs exist", value="")]
    else:
      role_choices=[discord.app_commands.Choice(name=gang.name, value=str(gang.id)) for gang in self.get_all_gangs(guild)]
    return role_choices

  def get_gang_df(self, gang_name: str | int) -> pd.DataFrame:
    if type(gang_name) == int:
      gang_name = get_df_at(self.bot_df, gang_name, "RID", "Name")

    log.info(f"Getting '{gang_name}' as dataframe...")
    for worksheet in self.worksheets:
      if worksheet.title == gang_name:
        return get_as_dataframe(worksheet)
    raise Exception(f"Couldn't find gang called {gang_name}")

  def get_rid(self, rolename: str) -> str:
    id: str = get_df_at(self.bot_df, rolename, "Name", "RID")
    return id

  def get_all_RIDs(self) -> list[str]:
    return self.bot_df['RID'].to_list()

  def get_all_gangs(self, guild: discord.Guild) -> list[discord.Role]:
    log.info("Getting all gangs...")
    all_RIDs = self.get_all_RIDs()
    return [get_role(guild, rid) for rid in all_RIDs]

  def get_gangs(self, member: discord.Member) -> list[discord.Role]:
    gang_roles = self.bot_df['Name'].to_list()
    matching_gangs = [role for role in member.roles if role.name in gang_roles]
    return matching_gangs

  def get_cid(self, role: discord.Role) -> str:
    log.info(f"Getting CID for @{role.name}")
    cid = get_df_at(self.bot_df, role.id, "RID", "CID")
    return cid

  def get_worksheet_index(self, sheetname: str) -> int:
    for worksheet in self.worksheets:
      if worksheet.title == sheetname:
        return self.worksheets.index(worksheet)
    raise Exception(f"Couldn't find worksheet called {sheetname}")

  def get_crids(self, role: discord.Role) -> dict[str, int]:
    log.info(f"Getting subroles for @{role.name}")
    crids: dict[str, int] = get_df_at(self.bot_df, role.id, "RID", "CRIDs", read_dict=True)
    return crids

  def get_subroles(self, role: discord.Role, guild: discord.Guild) -> list[discord.Role]:
    roles = []
    for crid in self.get_crids(role):
      found = guild.get_role(int(crid))
      if not found:
        log.error(f"Failed to get role with ID: {crid}")
        continue
      roles.append(found)
    return roles

  def get_subrole(self, role: discord.Role, member: discord.Member, exclude: discord.Role | None = None) -> discord.Role | None:
    subrole_ids = [sub.id for sub in self.get_subroles(role, member.guild)]
    for member_role in member.roles:
      if member_role.id in subrole_ids:
        if exclude:
          if exclude.id != member_role.id:
            return member_role
        else:
          return member_role
    log.warning(f"@{member.name} does not have a subrole")

  def get_gang_from_subrole(self, guild: discord.Guild, role: discord.Role) -> discord.Role:
    gang_name = role.name.split('-')[0].strip()
    rid = get_df_at(self.bot_df, gang_name, "Name", "RID")
    gang_role = guild.get_role(int(rid))
    if not gang_role: raise Exception(f"Failed to get role with ID {rid}")
    return gang_role

  async def create_role(self, guild: discord.Guild, roleName: str, hoisted: bool = True) -> discord.Role:
    log.info(f"Creating role @{roleName}...")
    newRole = await guild.create_role(name=roleName, hoist=hoisted, mentionable=True)

    subrole = 0
    if not hoisted:
      subrole = len(self.sheetnames)

    roleMap = {newRole: 1 + subrole}
    for i,role in enumerate (guild.roles):
      roleMap [role] = i + 2 + subrole

    await guild.edit_role_positions(roleMap) # type: ignore
    return newRole

  async def create_subroles(self, guild: discord.Guild, role: discord.Role, rmap: dict[str, int]) -> dict[str, int]:
    newMap: dict[str, int] = {}

    for key, value in rmap.items():
      newName = f"{role.name} - {key}"
      power = value

      newRole = await self.create_role(guild, newName, hoisted=False)
      newMap[str(newRole.id)] = power
    return newMap

  def create_sheet(self, worksheetName: str) -> Worksheet:
    if worksheetName in self.sheetnames:
      raise Exception(f"Cannot create - worksheet '{worksheetName}' already exists")

    log.info(f"Creating worksheet '{worksheetName}'...")
    newSheet = self.spreadsheet.add_worksheet(
      title=worksheetName,
      rows=2,
      cols=len(GANG_DATA_HEADERS),
      index=len(self.sheetnames))
    log.info(f"Created worksheet '{worksheetName}'")
    dataframe = pd.DataFrame(columns=GANG_DATA_HEADERS)
    set_with_dataframe(newSheet, dataframe, resize=True)

    self.worksheets.append(newSheet)
    self.sheetnames.append(newSheet.title)
    self.sheetids.append(newSheet.id)
    self.spreadsheet.fetch_sheet_metadata()
    return newSheet

  def update_bot(self,
                 role: discord.Role,
                 gang_map: dict[str, int] | None = None,
                 roster_cid: int | None = None,
                 radio_cid: int | None = None,
                 category: discord.CategoryChannel | None = None) -> pd.DataFrame:
    log.info(f"Updating database...")
    if BOT_DATA_HEADERS != self.bot_df.columns.tolist():
      raise Exception(f"'bot_data' does not have the correct headers")

    name = role.name
    rid = str(role.id)
    mids = [mem.id for mem in role.members]
    modified = date.today()

    if category:
      cid = str(category.id)
    else:
      cid = self.get_cid(role)

    if gang_map:
      gmap = str(gang_map)
    else:
      gmap = str(self.get_crids(role))

    if roster_cid:
      rocid = str(roster_cid)
    else:
      rocid = str(get_df_at(self.bot_df, rid, "RID", "RoCID"))

    if roster_cid:
      racid = str(radio_cid)
    else:
      racid = str(get_df_at(self.bot_df, rid, "RID", "RaCID"))

    row = get_df_row(self.bot_df, role.id, "RID")
    if len(row) < 1:
      log.info(f"Role {role.name} is new to '{self.bot_sheet.title}'")
      row = len(self.bot_df)
      created = modified
    else:
      created = get_df_at(self.bot_df, role.id, "RID", "Created")

    role_data = [name, rid, cid, rocid, racid, mids, gmap, created, modified]
    self.bot_df.loc[row] = role_data

    set_with_dataframe(self.bot_sheet, self.bot_df, resize=True)
    log.info("Update successful")
    return self.bot_df

  def update_gang(self,
                  gang_name: str,
                  member: discord.Member,
                  delete: bool) -> pd.DataFrame:
    log.info(f"Updating worksheet '{gang_name}'...")
    worksheet = self.worksheets[self.get_worksheet_index(gang_name)]
    dataframe = self.get_gang_df(gang_name)

    if GANG_DATA_HEADERS != dataframe.columns.tolist():
      raise Exception(f"'{gang_name}' does not have the correct headers")

    if delete:
      dataframe = dataframe.loc[dataframe['ID'] != str(member.id)]
      set_with_dataframe(worksheet, dataframe, resize=True)
      log.info("Update successful")
      return dataframe

    for gang in self.get_all_gangs(member.guild):
      if gang.name == gang_name:
        gang_role = gang
        break
    if not gang_role:
      raise Exception(f"@{member.name} does not belong to @{gang_name}")

    crids: dict[str, int] = get_df_at(self.bot_df, gang_role.id, "RID", "CRIDs", read_dict=True)
    power = self.get_power(member, crids, skipAdmin=True)
    if power < 1:
      raise Exception(f"User doesn't have a subrole")

    subrole = get_role(member.guild, list(crids.keys())[list(crids.values()).index(power)])

    mid = str(member.id)
    name = member.nick if member.nick else member.name
    rank = subrole.name.split('-')[1].strip()
    rid = str(subrole.id)

    row = get_df_row(dataframe, member.id, "ID")
    if len(row) < 1:
      log.info(f"Member {name} is new to '{gang_name}'")
      row = len(dataframe)
      iban = "None"
    else:
      iban = get_df_at(dataframe, member.id, "ID", "IBAN")

    member_data = [mid, name, rank, rid, iban]
    dataframe.loc[row] = member_data
    dataframe.sort_values(by="RID",
                                 inplace=True,
                                 ascending=False,
                                 key=lambda values: [crids.get(value) for value in values.tolist()])

    set_with_dataframe(worksheet, dataframe, resize=True)
    log.info("Update successful")
    return dataframe

  async def update_roster(self, channel: discord.TextChannel, role: discord.Role, df: pd.DataFrame | None = None) -> None:
    if df is None:
      df = self.get_gang_df(role.name)
    printable = df[["Name", "Rank", "IBAN"]]

    output = t2a(
      header = printable.columns.tolist(),
      body = printable.values.tolist(),
      style = PresetStyle.thin_compact,
      alignments = [Alignment.LEFT, Alignment.LEFT, Alignment.RIGHT],
      first_col_heading = True
      )
    worksheet = self.worksheets[self.get_worksheet_index(role.name)]
    set_with_dataframe(worksheet, df)
    await self.update_roster_message(channel, output, role)

  async def update_roster_message(self, channel: discord.TextChannel, content: str, role: discord.Role) -> None:
    view = discord.ui.View()

    async def refresh_callback(interaction: discord.Interaction) -> None:
      await self.refresh_roster(role)
      await interaction.response.edit_message(view=view)
    refresh = discord.ui.Button(style=discord.ButtonStyle.success, label="Refresh")
    refresh.callback = refresh_callback
    view.add_item(refresh)

    async def subroles_callback(interaction: discord.Interaction) -> None:
      member = interaction.user
      if not self.can_execute(member, 4, role): # type: ignore
        await interaction.response.send_message(embed=permission_embed, ephemeral=True)
        return
      await interaction.response.send_modal(ChangeSubrolesModal(role, self, buttonPressed=True))
    subroles = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Change Subroles")
    subroles.callback = subroles_callback
    view.add_item(subroles)

    async def iban_callback(interaction:discord.Interaction) -> None:
      await interaction.response.send_modal(ChangeIBANModal(role, self, buttonPressed=True))
    iban = discord.ui.Button(style=discord.ButtonStyle.blurple, label="Set IBAN")
    iban.callback = iban_callback
    view.add_item(iban)

    last = [message async for message in channel.history(limit = 1, oldest_first=True)][0]
    if last and last.author.id == int(BOT_ID):
        await last.edit(content=f"{role.mention}\n```{content}```", view=view)
    else:
        log.info(f"Roster message not found - creating...")
        await channel.purge()
        await channel.send(f"{role.mention}\n```{content}```", view=view, silent=True)

  async def update_radio_message(self, channel: discord.TextChannel, role: discord.Role, embed: discord.Embed) -> None:
    view = discord.ui.View()

    async def radio_callback(interaction: discord.Interaction) -> None:
      member = interaction.user
      if not self.can_execute(member, 3, role): # type: ignore
        await interaction.response.send_message(embed=permission_embed, ephemeral=True)
        return
      await interaction.response.send_modal(ChangeRadioModal(role, self, True))
    radio = discord.ui.Button(style=discord.ButtonStyle.blurple, label="Change Radio")
    radio.callback = radio_callback
    view.add_item(radio)

    last = [message async for message in channel.history(limit = 1, oldest_first=True)][0]
    if last and last.author.id == int(BOT_ID):
        await last.edit(embed=embed, view=view)
    else:
        log.info(f"Radio message not found - creating...")
        await channel.purge()
        await channel.send(embed=embed, view=view, silent=True)

  def delete_sheet(self, sheetname: str, role: discord.Role | None = None) -> None:
    if role:
      log.info(f"Removing gang '{sheetname}' from database...")
      self.bot_df = self.bot_df.loc[self.bot_df['RID'] != str(role.id)]
      set_with_dataframe(self.bot_sheet, self.bot_df, resize=True)

    log.info(f"Deleting worksheet '{sheetname}'...")
    for i, worksheet in enumerate(self.worksheets):
      if worksheet.title == sheetname:
        self.worksheets.pop(i)
        self.sheetnames.pop(i)
        self.sheetids.pop(i)
        self.spreadsheet.del_worksheet(worksheet)
        return
    raise Exception(f"Couldn't find worksheet called {sheetname}")

  def reset_data(self) -> None:
    clr_req = [{
      "deleteRange": {
        "range": {
          "sheetId": self.bot_sheet.id,
          "startRowIndex": 1},
        "shiftDimension": "ROWS"}}]
    del_req = [{"deleteSheet": {"sheetId": ws.id}}
        for ws in self.worksheets]

    reqs = clr_req + del_req

    log.info(f"Deleting {len(self.worksheets)} worksheets...")
    self.spreadsheet.batch_update({"requests": reqs})
    self.__init__(self.SPREADSHEET_ID)

  async def refresh_roster(self, role: discord.Role) -> None:
    log.info(f"Refreshing @{role.name} roster...")

    worksheet = self.worksheets[self.get_worksheet_index(role.name)]
    crids: dict[str, int] = get_df_at(self.bot_df, role.id, "RID", "CRIDs", read_dict=True)

    dataframe = pd.DataFrame(columns=GANG_DATA_HEADERS)
    for member in role.members:
      power = self.get_power(member, crids, skipAdmin=True)
      if power < 1:
        raise Exception(f"User doesn't have a subrole")
      subrole = get_role(member.guild, list(crids.keys())[list(crids.values()).index(power)])

      mid = str(member.id)
      name = member.name if not member.nick else member.nick
      rank = subrole.name.split('-')[1].strip()
      rid = str(subrole.id)

      try:
        iban = get_df_at(self.get_gang_df(role.name), member.id, "ID", "IBAN")
      except Exception:
        log.error(f"Could not get IBAN for {member.id} - setting to None")
        iban = "None"

      dataframe.loc[len(dataframe)] = [mid, name, rank, rid, iban]
    set_with_dataframe(worksheet, dataframe, resize=True)

    rocid = get_df_at(self.bot_df, role.id, "RID", "RoCID")
    channel: TextChannel = role.guild.get_channel(int(rocid)) # type: ignore
    if not channel: raise Exception("Could not find roster channel")
    await self.update_roster(channel, role, dataframe)

  async def assign_iban(self, role: discord.Role, member: discord.Member | discord.User, iban: str) -> None:
    dataframe = self.get_gang_df(role.name)
    dataframe.loc[dataframe["ID"] == str(member.id), "IBAN"] = iban

    rocid = get_df_at(self.bot_df, role.id, "RID", "RoCID")
    channel: TextChannel = role.guild.get_channel(int(rocid)) # type: ignore
    if not channel: raise Exception("Could not find roster channel")

    await self.update_roster(channel, role, dataframe)

  def can_execute(self,
                  caller: discord.Member,
                  requirement: int,
                  role: discord.Role | None,
                  isEvent: bool = False) -> bool:
    if not role:
      return True if isAdmin(caller) else False

    if isEvent:
        gang_role = self.get_gang_from_subrole(caller.guild, role)
        if gang_role not in caller.roles:
            log.warning(f"@{caller.name} does not have permission to use this command")
            return False
        return True if self.get_power(caller, self.get_crids(gang_role)) >= requirement else False
    return True if self.get_power(caller, self.get_crids(role)) >= requirement else False

class ChangeIBANModal(discord.ui.Modal):
  def __init__(self, gang: discord.Role, db: Database, buttonPressed: bool = False) -> None:
    self.gang = gang
    self.db = db
    self.buttonPressed = buttonPressed
    super().__init__(title="Enter IBAN")

  iban = discord.ui.TextInput(
    label="You can find yours at any bank location!",
    placeholder="OK123123",
    max_length = 8,
    min_length = 8,
    required=True,
    row = 0
  )

  async def on_submit(self, interaction: discord.Interaction) -> None:
    regex = re.search(pattern="OK[0-9]{6}", string=str(self.iban).upper())
    if not regex:
      await interaction.response.send_message(embed=discord.Embed(title="Improperly Formatted IBAN", description="The value you entered is not a valid IBAN", color=self.gang.color), ephemeral=True)
      return
    await self.db.assign_iban(self.gang, interaction.user, str(self.iban).upper())
    if self.buttonPressed:
      await interaction.response.defer(thinking=False)
    else:
      await interaction.response.send_message(embed=discord.Embed(title="IBAN Changed", color=discord.Colour.dark_green()), ephemeral=True)

class ChangeSubrolesModal(discord.ui.Modal):
  def __init__(self, gang: discord.Role, db: Database, buttonPressed: bool = False) -> None:
    self.gang = gang
    self.db = db
    self.buttonPressed = buttonPressed
    super().__init__(title="Change Subroles Names")

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
    guild = interaction.guild
    if not guild: raise Exception("Failed to get guild")

    subroles = self.db.get_subroles(self.gang, guild)
    pre = f"{self.gang.name} -"
    await subroles[0].edit(name=f"{pre} {self.gl_name}")
    await subroles[1].edit(name=f"{pre} {self.hc_name}")
    await subroles[2].edit(name=f"{pre} {self.m_name}")
    await subroles[3].edit(name=f"{pre} {self.ha_name}")

    await self.db.refresh_roster(self.gang)
    if self.buttonPressed:
      await interaction.response.defer(thinking=False)
    else:
      await interaction.response.send_message(embed=discord.Embed(title="Subroles Changed", color=discord.Colour.dark_green()), ephemeral=True)

class ChangeRadioModal(discord.ui.Modal):
  def __init__(self, role: discord.Role, db: Database, buttonPressed: bool = False):
    self.role = role
    self.db = db
    self.buttonPressed = buttonPressed
    super().__init__(title="Set Radio Channels")

  primary=discord.ui.TextInput(
    label="What is your primary radio channel?",
    style=discord.TextStyle.short,
    placeholder="11.11",
    required=True,
    row = 0
  )
  secondary = discord.ui.TextInput(
    label="What is your secondary radio channel?",
    style=discord.TextStyle.short,
    placeholder="22.22",
    required=True,
    row = 0
  )
  tertiary = discord.ui.TextInput(
    label="What is your tertiary radio channel?",
    style=discord.TextStyle.short,
    placeholder="33.33",
    required=True,
    row = 0
  )
  notes = discord.ui.TextInput(
    label="Do you have any notes/instructions for radio channel usage?",
    style=discord.TextStyle.long,
    placeholder="Notes...",
    required=False,
    row = 0
  )

  async def on_submit(self, interaction: discord.Interaction) -> None:
    if str(self.primary).replace('.','',1).isdigit() and str(self.secondary).replace('.','',1).isdigit() and str(self.tertiary).replace('.','',1).isdigit():
      embed = discord.Embed(
        title=f"Radio Channels - {self.role.name}",
        description="*These are **private** radio channels, please do not share*", color=self.role.color)
      embed.add_field(name="Primary:", value=str(self.primary), inline=False)
      embed.add_field(name="Secondary:", value=str(self.secondary), inline=False)
      embed.add_field(name="Tertiary:", value=str(self.tertiary), inline=False)
      if self.notes:
        embed.add_field(name="Notes:", value=str(self.notes), inline=False)

      racid = get_df_at(self.db.bot_df, self.role.id, "RID", "RaCID")
      channel: TextChannel = self.role.guild.get_channel(int(racid)) # type: ignore
      if not channel: raise Exception("Could not find radio channel")
      await self.db.update_radio_message(channel, self.role, embed)

      if self.buttonPressed:
        await interaction.response.defer(thinking=False)
      else:
        await interaction.response.send_message(embed=discord.Embed(title="Radio Updated", color=discord.Colour.dark_green()), ephemeral=True)

    else:
      # Error here
      temp = 1