import os
import pandas as pd
from gspread import Spreadsheet, Worksheet, service_account
from gspread_dataframe import set_with_dataframe
from discord import Role, Member, CategoryChannel
from dotenv import load_dotenv
from datetime import date
from utility import ROLES, get_power
import logger
log = logger.Logger()

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
# RID = Role ID, CID = Category ID, MIDS= Member IDs (list)
BOT_DATA_HEADERS = ["Name", "RID", "CID", "MIDS", "Created", "Modified"]
GANG_DATA_HEADERS = ["ID", "Name", "Rank"]
LOCAL_ROLES = ROLES.copy()
LOCAL_ROLES.pop("ADMIN")

spreadsheet: Spreadsheet | None = None

def db_healthy() -> bool:
    if "private_key.json" not in os.listdir("private/"):
        log.fatal("private_key.json not found in the private/ directory")
        return False

    if not SPREADSHEET_ID:
        log.fatal("Unable to get SPREADSHEET_ID")
        return False

    worksheets = __connect()
    # This should never be true, checked in above function at start
    if not spreadsheet:
        return False

    if not worksheets:
        log.fatal("Global spreadsheet not found")
        return False

    sheetnames = [ws.title for ws in spreadsheet.worksheets()]

    try:
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
        return True

    except Exception as e:
        log.fatal(f"Couldn't open spreadsheet ({SPREADSHEET_ID})\n\n{e}")
        return False

def __connect() -> list[Worksheet] | None:
    try:
        global spreadsheet

        if not SPREADSHEET_ID:
            log.fatal("Unable to get SPREADSHEET_ID")
            return

        spreadsheet = service_account(filename="private/private_key.json") \
                  .open_by_key(SPREADSHEET_ID)
        if not spreadsheet:
            log.fatal("Global spreadsheet not found")
            return

        log.info(f"Connected to spreadsheet {spreadsheet.id} ({spreadsheet.title})")

        worksheets = [ws.title for ws in spreadsheet.worksheets()]
        log.info(f"Found worksheets - {worksheets}")
        return spreadsheet.worksheets()

    except Exception as e:
        log.error(f"Couldn't open the spreadsheet\n\n{e}")
        return

def reset_spreadsheet() -> bool:
    # This should never be true, checked in above function at start
    if not spreadsheet:
        return False

    worksheets = spreadsheet.worksheets()

    reqs = [
        {"repeatCell": {
            "range": {"sheetId": s.id},
            "fields": "*"}}
        if i == len(worksheets)-1 else
        {"deleteSheet": {"sheetId": s.id}}
        for i, s in enumerate(worksheets)]

    try:
        log.info("Deleting gang spreadsheets...")
        spreadsheet.batch_update({"requests": reqs})
        log.info("Resetting bot_data headers...")
        bot_data = get_worksheet("bot_data")
        dataframe = pd.DataFrame(columns=BOT_DATA_HEADERS)
        set_with_dataframe(bot_data, dataframe, resize=True)
        log.info("Spreadsheet reset complete")
        return True

    except Exception as e:
        log.error(f"Failed to reset database\n\n{e}")
        return False

def get_worksheet(worksheetName: str) -> Worksheet | None:
    # This should never be true, checked in above function at start
    if not spreadsheet:
        return

    sheetnames = [ws.title for ws in spreadsheet.worksheets()]

    if not sheetnames or worksheetName not in sheetnames:
        log.error(f"Cannot get - worksheet '{worksheetName}' does not exist")
        return

    return spreadsheet.worksheet(worksheetName)

def get_worksheets() -> list[Worksheet] | None:
    return __connect()

def create_worksheet(worksheetName: str) -> Worksheet | None:
    # This should never be true, checked in above function at start
    if not spreadsheet:
        return

    sheetnames = [ws.title for ws in spreadsheet.worksheets()]
    if not sheetnames or worksheetName in sheetnames:
        log.error(f"Cannot create - worksheet '{worksheetName}' already exists")
        return spreadsheet.worksheet(worksheetName)

    try:
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

    except Exception as e:
        log.error(f"Create worksheet '{worksheetName}' failed\n\n{e}")
        return

def delete_worksheet(worksheetName: str, role: Role | None = None) -> bool:
    # This should never be true, checked in above function at start
    if not spreadsheet:
        return False

    sheetnames = [ws.title for ws in spreadsheet.worksheets()]
    if not sheetnames or worksheetName not in sheetnames:
        log.warning(f"Cannot delete - worksheet '{worksheetName}' does not exist")
        return True

    try:
        if role:
            log.info("Attempting to update worksheet 'bot_data' ...")

            worksheet = get_worksheet("bot_data")
            if not worksheet:
                log.warning("Update worksheet 'bot_data' failed")

            else:
                values = worksheet.get_values()
                dataframe = pd.DataFrame(values[1:], columns=values[0])
                dataframe = dataframe.loc[dataframe['RID'] != str(role.id)]
                set_with_dataframe(worksheet, dataframe, resize=True)
                log.info("Updated worksheet 'bot_data'")

        log.info(f"Attempting to delete worksheet '{worksheetName}'...")
        spreadsheet.del_worksheet(get_worksheet(worksheetName))
        log.info(f"Deleted worksheet '{worksheetName}'")
        return True

    except Exception as e:
        log.error(f"Delete worksheet '{worksheetName}' failed\n\n{e}")
        return False

def update_worksheet(worksheet: Worksheet,
                    member: Member | None = None,
                    role: Role | None = None,
                    category: CategoryChannel | None = None) -> Worksheet:
    try:
        log.info(f"Updating worksheet '{worksheet.title}'...")

        values = worksheet.get_values()
        dataframe = pd.DataFrame(values[1:], columns=values[0])

        if member:
            log.info("Updating with member data...")
            if get_power(member, LOCAL_ROLES) < 1:
                log.error(f"User doesn't have a role")
                return worksheet

            if GANG_DATA_HEADERS != dataframe.columns.tolist():
                log.error(f"'{worksheet.title}' does not have the correct headers for member modification. Was the wrong sheet sent?")
                return worksheet

            mid = str(member.id)
            name = member.nick if member.nick else member.name
            rank = list(LOCAL_ROLES.keys())[list(LOCAL_ROLES.values()).index(get_power(member, LOCAL_ROLES))]
            member_data = [mid, name, rank]

            row_index = dataframe.index[dataframe['ID'] == mid].tolist()
            if len(row_index) < 1:
                log.info(f"Member {name} is new to '{worksheet.title}'")
                row_index = len(dataframe)
            dataframe.loc[row_index] = member_data

            log.info(f"'{worksheet.title}' updated with member data")

        if not role or not category:
            log.error("Missing role or category in call")
            return worksheet

        else:
            if BOT_DATA_HEADERS != dataframe.columns.tolist():
                log.error(f"'{worksheet.title}' does not have the correct headers for role modification. Was the wrong sheet sent?")
                return worksheet

            name = role.name
            rid = str(role.id)
            mids = [member.id for member in role.members]
            modified = date.today()
            cid = str(category.id)

            row_index = dataframe.index[dataframe['RID'] == str(role.id)].tolist()
            if len(row_index) < 1:
                log.info(f"Role {role.name} is new to '{worksheet.title}'")
                row_index = len(dataframe)
                created = modified
            else:
                created = dataframe.loc[dataframe["RID"] == str(role.id), "Created"][0]

            role_data = [name, rid, cid, mids, created, modified]
            dataframe.loc[row_index] = role_data

            log.info(f"'{worksheet.title}' updated with role and category data")

        set_with_dataframe(worksheet, dataframe, resize=True)
        return worksheet

    except Exception as e:
        log.error(f"Something went wrong while updating the worksheet\n\n{e}")
        return worksheet

def get_category_id(role: Role) -> str | None:
    log.info(f"Getting CID for '{role.name}'...")

    worksheet = get_worksheet('bot_data')
    if not worksheet:
        return
    try:
        values = worksheet.get_values()
        dataframe = pd.DataFrame(values[1:], columns=values[0])
        cid = dataframe.loc[dataframe["RID"] == str(role.id), "CID"][0]

        log.info(f"Found CID: {cid}")
        return cid
    except:
        log.error(f"Something went wrong getting CID")
        return

def gangInDB(role: Role) -> bool:
    worksheet = get_worksheet("bot_data")
    if not worksheet:
        log.error("Failed to get bot_data worksheet")
        return False

    values = worksheet.get_values()
    dataframe = pd.DataFrame(values[1:], columns=values[0])
    print(dataframe)
    return True

# https://github.com/robin900/gspread-dataframe
