import os
from typing import Any
import pandas as pd
from gspread import Spreadsheet, Worksheet, service_account
from gspread_dataframe import set_with_dataframe
from discord import Guild, Role, Member, CategoryChannel
from dotenv import load_dotenv
from datetime import date
from utility import ROLES, get_power, get_role
import logger
log = logger.Logger()

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
# RID = Role ID, CID = Category ID, MIDS= Member IDs (list)
BOT_DATA_HEADERS = ["Name", "RID", "CID", "MIDS", "Map", "Created", "Modified"]
GANG_DATA_HEADERS = ["ID", "Name", "Rank", "IBAN"]
LOCAL_ROLES = ROLES.copy()
LOCAL_ROLES.pop("ADMIN")

if not SPREADSHEET_ID:
            raise Exception("Unable to get SPREADSHEET_ID")
spreadsheet: Spreadsheet = service_account(filename="private/private_key.json") \
                  .open_by_key(SPREADSHEET_ID)

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

def get_worksheets() -> list[Worksheet]:
    try:
        worksheets = [ws.title for ws in spreadsheet.worksheets()]
        log.info(f"Found worksheets - {worksheets}")
        return spreadsheet.worksheets()

    except Exception as e:
        raise e

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
        cid = dataframe.loc[dataframe["RID"] == str(role.id), "CID"].to_string().split()[1]

    if gang_map:
        gmap = gang_map
    else:
        gmap = dataframe.loc[dataframe["RID"] == str(role.id), "Map"].to_string().split()[1]

    row_index = dataframe.index[dataframe['RID'] == str(role.id)].tolist()
    if len(row_index) < 1:
        log.info(f"Role {role.name} is new to '{worksheet.title}'")
        row_index = len(dataframe)
        created = modified

    else:
        created = dataframe.loc[dataframe["RID"] == str(role.id), "Created"].to_string().split()[1]


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

    if get_power(member, LOCAL_ROLES) < 1:
        raise Exception(f"User doesn't have a role")

    mid = str(member.id)
    name = member.nick if member.nick else member.name
    rank = list(LOCAL_ROLES.keys())[list(LOCAL_ROLES.values()).index(get_power(member, LOCAL_ROLES))]

    row_index = dataframe.index[dataframe['ID'] == mid].tolist()
    if len(row_index) < 1:
        log.info(f"Member {name} is new to '{sheetname}'")
        row_index = len(dataframe)
        iban = "None"
    else:
        iban = dataframe.loc[dataframe["ID"] == mid, "IBAN"].to_string().split()[1]

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
    cid = dataframe.loc[dataframe["RID"] == str(role.id), "CID"].to_string().split()[1]

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

# def row_exists(dataframe: pd.DataFrame, id: int) -> bool:
#     if dataframe.empty:
#         return False

#     res = dataframe.loc[dataframe['RID'] == str(id)]
#     if res.empty:
#         return False

#     return True

def change_role_map():
    return