from urllib import request
import discord
from gspread import Spreadsheet, Worksheet, service_account
from gspread_dataframe import set_with_dataframe
from utility import get_role
import pandas as pd
from logger import Logger
log = Logger()

BOT_DATA_HEADERS = ["Name", "RID", "CID", "MIDs", "CRIDs", "Created", "Modified"]
GANG_DATA_HEADERS = ["ID", "Name", "Rank", "IBAN"]

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

def get_as_dataframe(worksheet: Worksheet) -> pd.DataFrame:
  values = worksheet.get_values()
  dataframe = pd.DataFrame(values[1:], columns=values[0])
  return dataframe

def get_dataframe_at(input: pd.DataFrame, id: int, value: str):
  return eval(input.loc[input["RID"] == str(id), value].array[0])

class Database:
  def __init__(self, SPREADSHEET_ID: str):
    self.SPREADSHEET_ID = SPREADSHEET_ID
    self.spreadsheet = connect_to_db(SPREADSHEET_ID)
    self.worksheets = self.spreadsheet.worksheets()

    self.sheetnames = [ws.title for ws in self.worksheets]
    self.sheetids = [ws.id for ws in self.worksheets]

    self.bot_sheet = self.worksheets.pop(self.get_worksheet_index('bot_data'))
    self.bot_df = get_as_dataframe(self.bot_sheet)

    print(self.worksheets)
    print(self.bot_sheet)
    log.info("Database initialized")

  def get_power(self):
    return

  def get_gang_df(self, gang_name: str) -> pd.DataFrame:
    log.info(f"Getting {gang_name} dataframe...")
    for worksheet in self.worksheets:
      if worksheet.title == gang_name:
        return get_as_dataframe(worksheet)
    raise Exception(f"Couldn't find gang called {gang_name}")

  def get_all_gangs(self, guild: discord.Guild) -> list[discord.Role]:
    log.info("Getting all gangs...")
    all_RIDs = self.bot_df['RID'].to_list()
    return [get_role(guild, rid) for rid in all_RIDs]

  def get_category_id(self, role: discord.Role) -> str:
    log.info(f"Getting CID for @{role.name}")
    cid = get_dataframe_at(self.bot_df, role.id, "CID")
    return cid

  def get_worksheet_index(self, sheetname: str) -> int:
    for worksheet in self.worksheets:
      if worksheet.title == sheetname:
        return self.worksheets.index(worksheet)
    raise Exception(f"Couldn't find worksheet called {sheetname}")

  def get_subrole_ids(self, role: discord.Role) -> dict[str, str]:
    log.info(f"Getting subroles for @{role.name}")
    subrole_ids: dict[str, str] = get_dataframe_at(self.bot_df, role.id, "CRIDs")
    return subrole_ids

  def update_bot(self, ):
    return

  def update_gang(self):
    return

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
    return newSheet

  async def create_role(self,
                        guild: discord.Guild,
                        roleName: str,
                        hoisted: bool = True) -> discord.Role:
    newRole = await guild.create_role(name=roleName, hoist=hoisted, mentionable=True)
    return newRole

  async def create_category(self,
                            guild: discord.Guild,
                            role: discord.Role) -> discord.CategoryChannel:
    categories = [category.name for category in guild.categories]
    categories.append(role.name)
    categories.sort()

    newCategory = await guild.create_category(
      role.name,
      overwrites= {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        role: discord.PermissionOverwrite(read_messages=True)
      },
      position=categories.index(role.name))

    return newCategory

  async def create_subroles(self,
                            guild: discord.Guild,
                            role: discord.Role,
                            rmap: dict[str, str]) -> dict[str, str]:
    newMap: dict[str, str] = {}
    for key, value in rmap.items():
      newName = f"{role.name} - {value}"
      power = rmap.get(key)

      if not power:
        raise Exception(f"Could not find {key} in role map")

      newRole = await self.create_role(guild, newName, hoisted=False)
      newMap[str(newRole.id)] = power
    return newMap

  def delete_sheet(self, sheetname: str) -> None:
    log.info(f"Deleting {sheetname} dataframe...")
    for i, worksheet in enumerate(self.worksheets):
      if worksheet.title == sheetname:
        self.worksheets.pop(i)
        self.spreadsheet.del_worksheet(worksheet)
    raise Exception(f"Couldn't find worksheet called {sheetname}")

  def reset_data(self) -> None:
    reqs = [
        {"deleteRange": {
            "range": {"sheetId": self.bot_sheet.id,
              "startRowIndex": 1}}},
        [{"deleteSheet": {"sheetId": ws.id}}
        for ws in self.worksheets]]

    log.info(f"Deleting {len(self.worksheets)} worksheets...")
    self.spreadsheet.batch_update({"requests": reqs})
    self.__init__(self.SPREADSHEET_ID)

