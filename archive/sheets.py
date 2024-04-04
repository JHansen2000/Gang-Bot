import os
import pandas as pd
from gspread import Spreadsheet, Worksheet, service_account
from gspread_dataframe import set_with_dataframe
from discord import Guild, Role, Member, CategoryChannel
from dotenv import load_dotenv
from datetime import date
from utility import get_role
import logger
log = logger.Logger()

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
ADMIN_ID = os.getenv("ADMIN_ID")
# RID=Role ID, CID=Category ID, MIDs=Member IDs (list), CRIDs=Custom Role IDs (list)
BOT_DATA_HEADERS = ["Name", "RID", "CID", "MIDs", "CRIDs", "Created", "Modified"]
GANG_DATA_HEADERS = ["ID", "Name", "Rank", "IBAN"]

if not SPREADSHEET_ID: raise Exception("Unable to get SPREADSHEET_ID")
if not ADMIN_ID: raise Exception("Unable to get ADMIN_ID")

spreadsheet: Spreadsheet = service_account(filename="private/private_key.json") \
                  .open_by_key(SPREADSHEET_ID)

def isAdmin(member: Member)-> bool:
    admin_role = get_role(member.guild, ADMIN_ID)
    return True if admin_role in member.roles else False

def get_power(member: Member, roles: dict[str, str], skipAdmin: bool = False) -> int:
  print(member)
  print(roles)
  if not skipAdmin and isAdmin(member):
      log.info(f"@{member.name} is an admin")
      return 5

  power = 0
  for role in member.roles:
    role_power = roles.get(str(role.id))
    if role_power:
        power = max(int(role_power), power)
  log.info(f"@{member.name} has power {power}")
  return power

def can_execute(member: Member, required_power: int, target: Role | None = None) -> bool:
  if not target:
    if isAdmin(member):
        return True
    return False

  roles = get_CRIDs_dict(target)
  matching_gangs = get_gangs(member)

  if target not in matching_gangs and not isAdmin(member):
      log.warning(f"@{member.name} doesn't belong to @{target.name} gang")
      return False

  return True if get_power(member, roles) >= required_power else False

def db_healthy() -> None:
    if "private_key.json" not in os.listdir("private/"):
        raise Exception("private_key.json not found in the private/ directory")

    worksheets = get_worksheets()
    if not worksheets:
        raise Exception("Global spreadsheet not found")

    sheetnames = [ws.title for ws in spreadsheet.worksheets()]

    if "bot_data" not in sheetnames:
        log.warning("bot_data sheet not found - creating...")
        bot_data = spreadsheet.add_worksheet(
            title="bot_data",
            rows=1,
            cols=len(BOT_DATA_HEADERS),
            index=len(sheetnames))
        dataframe = pd.DataFrame(columns=BOT_DATA_HEADERS)
        set_with_dataframe(bot_data, dataframe, resize=True)
        log.info("bot_data sheet created")
    return



def reset_spreadsheet() -> None:
    worksheets = get_worksheets()
    reqs = [
        {"repeatCell": {
            "range": {"sheetId": s.id},
            "fields": "*"}}
        if i == len(worksheets)-1 else
        {"deleteSheet": {"sheetId": s.id}}
        for i, s in enumerate(worksheets)]

    log.info("Deleting gang spreadsheets...")
    spreadsheet.batch_update({"requests": reqs})
    log.info("Resetting bot_data headers...")
    bot_data = get_worksheet("bot_data")
    dataframe = pd.DataFrame(columns=BOT_DATA_HEADERS)
    set_with_dataframe(bot_data, dataframe, resize=True)
    log.info("Spreadsheet reset complete")
    return

def get_worksheet(worksheetName: str) -> Worksheet:
    sheetnames = [ws.title for ws in spreadsheet.worksheets()]
    if not sheetnames or worksheetName not in sheetnames:
        raise Exception(f"Cannot get - worksheet '{worksheetName}' does not exist")
    return spreadsheet.worksheet(worksheetName)

def create_worksheet(worksheetName: str) -> Worksheet:
    sheetnames = [ws.title for ws in get_worksheets()]
    if not sheetnames or worksheetName in sheetnames:
        raise Exception(f"Cannot create - worksheet '{worksheetName}' already exists")

    log.info(f"Attempting to create worksheet '{worksheetName}'...")
    newSheet = spreadsheet.add_worksheet(
        title=worksheetName,
        rows=2,
        cols=len(GANG_DATA_HEADERS),
        index=len(sheetnames) - 1)
    log.info(f"Created worksheet '{worksheetName}'")

    dataframe = pd.DataFrame(columns=GANG_DATA_HEADERS)
    set_with_dataframe(newSheet, dataframe, resize=True)
    return newSheet

def delete_worksheet(worksheetName: str, role: Role | None = None) -> None:
    if role:
        log.info("Attempting to update worksheet 'bot_data' ...")

        worksheet = get_worksheet("bot_data")
        values = worksheet.get_values()
        dataframe = pd.DataFrame(values[1:], columns=values[0])
        dataframe = dataframe.loc[dataframe['RID'] != str(role.id)]
        set_with_dataframe(worksheet, dataframe, resize=True)
        log.info("Updated worksheet 'bot_data'")

    log.info(f"Attempting to delete worksheet '{worksheetName}'...")
    spreadsheet.del_worksheet(get_worksheet(worksheetName))
    log.info(f"Deleted worksheet '{worksheetName}'")
    return

def update_data_worksheet(role: Role,
                          gang_map: dict[str, str] | None = None,
                          category: CategoryChannel | None = None
                          ) -> Worksheet:
    log.info(f"Updating worksheet 'bot_data'...")
    worksheet = get_worksheet('bot_data')
    dataframe = get_as_dataframe(worksheet)

    if BOT_DATA_HEADERS != dataframe.columns.tolist():
            raise Exception(f"'bot_data' does not have the correct headers")

    name = role.name
    rid = str(role.id)
    mids = [mem.id for mem in role.members]
    modified = date.today()

    if category:
        cid = str(category.id)
    else:
        cid = dataframe.loc[dataframe["RID"] == str(role.id), "CID"].array[0]

    if gang_map:
        gmap = gang_map
    else:
        gmap = dataframe.loc[dataframe["RID"] == str(role.id), "CRIDs"].array[0]

    row_index = dataframe.index[dataframe['RID'] == str(role.id)].tolist()
    if len(row_index) < 1:
        log.info(f"Role {role.name} is new to '{worksheet.title}'")
        row_index = len(dataframe)
        created = modified

    else:
        created = dataframe.loc[dataframe["RID"] == str(role.id), "Created"].array[0]


    role_data = [name, rid, cid, mids, gmap, created, modified]
    dataframe.loc[row_index] = role_data

    set_with_dataframe(worksheet, dataframe, resize=True)
    log.info("Update successful")
    return worksheet

def update_gang_worksheet(sheetname: str, member: Member, delete: bool) -> Worksheet:
    log.info(f"Updating worksheet '{sheetname}'...")
    worksheet = get_worksheet(sheetname)
    dataframe = get_as_dataframe(worksheet)

    if GANG_DATA_HEADERS != dataframe.columns.tolist():
        raise Exception(f"'{sheetname}' does not have the correct headers")

    if delete:
        dataframe = dataframe.loc[dataframe['ID'] != str(member.id)]
        set_with_dataframe(worksheet, dataframe, resize=True)
        log.info("Update successful")
        return worksheet

    gang_RIDs = get_gang_RIDs()
    gangs = [get_role(member.guild, rid) for rid in gang_RIDs]
    for gang in gangs:
        if gang.name == sheetname:
            gang_role = gang
    if not gang_role:
        raise Exception(f"User does not belong to @{worksheet}")

    crids = get_CRIDs_dict(gang_role)
    power = get_power(member, crids, skipAdmin=True)
    if power < 1:
        raise Exception(f"User doesn't have a subrole")

    subrole = get_role(member.guild, list(crids.keys())[list(crids.values()).index(str(power))])

    mid = str(member.id)
    name = member.nick if member.nick else member.name
    rank = subrole.name

    row_index = dataframe.index[dataframe['ID'] == mid].tolist()
    if len(row_index) < 1:
        log.info(f"Member {name} is new to '{sheetname}'")
        row_index = len(dataframe)
        iban = "None"
    else:
        iban = dataframe.loc[dataframe["ID"] == mid, "IBAN"].array[0]

    member_data = [mid, name, rank, iban]
    dataframe.loc[row_index] = member_data

    set_with_dataframe(worksheet, dataframe, resize=True)
    log.info("Update successful")
    return worksheet

def get_category_id(role: Role) -> str:
    log.info(f"Getting CID for '{role.name}'...")
    worksheet = get_worksheet('bot_data')

    values = worksheet.get_values()
    dataframe = pd.DataFrame(values[1:], columns=values[0])
    cid = dataframe.loc[dataframe["RID"] == str(role.id), "CID"].array[0]

    log.info(f"Found CID: {cid}")
    return cid

def get_as_dataframe(worksheet: Worksheet) -> pd.DataFrame:
    values = worksheet.get_values()
    dataframe = pd.DataFrame(values[1:], columns=values[0])
    return dataframe

def get_gangs(member: Member) -> list[Role]:
  dataframe = get_as_dataframe(get_worksheet('bot_data'))
  gang_roles = dataframe['Name'].to_list()
  matching_gangs = [role for role in member.roles if role.name in gang_roles]
  return matching_gangs

def get_all_gangs(guild: Guild) -> list[Role]:
    dataframe = get_as_dataframe(get_worksheet('bot_data'))
    gang_RIDs = dataframe['RID'].to_list()
    return [get_role(guild, rid) for rid in gang_RIDs]

def get_gang_RIDs() -> list[str]:
    dataframe = get_as_dataframe(get_worksheet('bot_data'))
    return dataframe['RID'].to_list()

def get_CRIDs_dict(role: Role) -> dict[str, str]:
    dataframe = get_as_dataframe(get_worksheet('bot_data'))
    CRIDs_dict: dict[str, str] = eval(dataframe.loc[dataframe["RID"] == str(role.id), "CRIDs"].array[0])
    return CRIDs_dict

def get_custom_roles(guild: Guild, CRIDs_dict: dict[str, str]) -> list[Role]:
    roles = []
    for crid in CRIDs_dict.keys():
        roles.append(guild.get_role(int(crid)))
    return roles



# def row_exists(dataframe: pd.DataFrame, id: int) -> bool:
#     if dataframe.empty:
#         return False

#     res = dataframe.loc[dataframe['RID'] == str(id)]
#     if res.empty:
#         return False

#     return True

def change_role_map():
    return