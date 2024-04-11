import os
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

async def update_roster(channel: discord.TextChannel, df: pd.DataFrame) -> None:
  printable = df[["Name", "Rank", "IBAN"]]

  output = t2a(
    header = printable.columns.tolist(),
    body = printable.values.tolist(),
    style = PresetStyle.thin_compact,
    alignments = [Alignment.LEFT, Alignment.LEFT, Alignment.RIGHT],
    first_col_heading = True
    )
  await channel.purge()
  await channel.send(f"```{output}```", silent=True)

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

    # self.print_vars()
    log.info("Database initialized")

  def print_vars(self) -> None:
    print('\n')
    print(self.SPREADSHEET_ID)
    print(self.spreadsheet)
    print(self.worksheets)
    print(self.sheetnames)
    print(self.sheetids)
    print(self.bot_sheet)
    print(self.bot_df)
    print('\n')

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

  def get_gang_choices(self) -> list[discord.app_commands.Choice[str]]:
    if len(self.sheetnames) < 1:
      role_choices=[discord.app_commands.Choice(name="No gangs exist", value="")]
    else:
      role_choices=[discord.app_commands.Choice(name=gang_name, value=self.get_rid(gang_name)) for gang_name in self.sheetnames]
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
