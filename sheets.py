import os
import pandas as pd
from gspread import Spreadsheet, Worksheet, service_account
from gspread_dataframe import set_with_dataframe
from discord import Role
from dotenv import load_dotenv
from datetime import date
import logger
log = logger.Logger()

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
# RID = Role ID, CID = Category ID, SID = Spreadsheet ID, MIDS= Member IDs (list)
BOT_DATA_HEADERS = ["Name", "RID", "CID", "SID", "MIDS", "Created", "Modified"]

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

def create_worksheet(worksheetName: str, role : Role | None = None) -> Worksheet | None:
    # This should never be true, checked in above function at start
    if not spreadsheet:
        return

    sheetnames = [ws.title for ws in spreadsheet.worksheets()]
    if not sheetnames or worksheetName in sheetnames:
        log.error(f"Cannot create - worksheet '{worksheetName}' already exists")
        return spreadsheet.worksheet(worksheetName)

    try:
        COLUMNS = ["Name", ]
        if role:
            log.info("Attempting to update 'bot_data' worksheet...")
            worksheet = get_worksheet("bot_data")
            if not worksheet:
                log.warning("Update worksheet 'bot_data' failed")
            else:
                data = [role.name, str(role.id), None, None, role.members, date.today(), date.today()]
                values = worksheet.get_values()
                dataframe = pd.DataFrame(values[1:], columns=values[0])
                dataframe.loc[len(dataframe)] = data
                set_with_dataframe(worksheet, dataframe, resize=True)
                log.info("Updated worksheet 'bot_data'")

        log.info(f"Attempting to create worksheet '{worksheetName}'...")
        newSheet = spreadsheet.add_worksheet(
            title=worksheetName,
            rows=1,
            cols=len(COLUMNS),
            index=len(sheetnames) - 1)
        log.info(f"Created worksheet '{worksheetName}'")
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
                dataframe = dataframe.loc[dataframe['ID'] != str(role.id)]
                print(dataframe)
                set_with_dataframe(worksheet, dataframe, resize=True)
                log.info("Updated worksheet 'bot_data'")

        log.info(f"Attempting to delete worksheet '{worksheetName}'...")
        spreadsheet.del_worksheet(get_worksheet(worksheetName))
        log.info(f"Deleted worksheet '{worksheetName}'")
        return True

    except Exception as e:
        log.error(f"Delete worksheet '{worksheetName}' failed\n\n{e}")
        return False

def gangInDB(role: Role) -> bool:
    worksheet = get_worksheet("bot_data")
    if not worksheet:
        log.error("Failed to get bot_data worksheet")
        return False

    dataframe = pd.DataFrame(worksheet.get_values()[1:], columns=worksheet.get_values()[0])
    print(dataframe)
    return True

# https://github.com/robin900/gspread-dataframe
