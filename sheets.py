import os
import gspread
import logger
from dotenv import load_dotenv
log = logger.Logger()

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

spreadsheet: gspread.Spreadsheet = None

def db_healthy() -> bool:
    if "private_key.json" not in os.listdir("private/"):
        log.fatal("private_key.json not found in the private/ directory")
        return False

    if not SPREADSHEET_ID:
        log.fatal("Unable to get SPREADSHEET_ID")
        return False

    worksheets = __connect()
    if not worksheets:
        log.fatal("Global spreadsheet not found")
        return False

    try:
        if "bot_data" not in worksheets:
             log.warning("bot_data sheet not found - creating...")
             spreadsheet.add_worksheet(title="bot_data", rows=1000, cols=1000, index=len(worksheets))
        return True

    except Exception as e:
        log.fatal(f"Couldn't open spreadsheet ({SPREADSHEET_ID})\n\n{e}")
        return False

def __connect() -> list[gspread.Worksheet] | None:
    try:
        global spreadsheet
        spreadsheet = gspread.service_account(filename="private/private_key.json") \
                  .open_by_key(SPREADSHEET_ID)
        if not spreadsheet:
            log.fatal("Global spreadsheet not found")
            return
        log.info(f"Connected to spreadsheet {spreadsheet.id} ({spreadsheet.title})")

        worksheets = [ws.title for ws in spreadsheet.worksheets()]
        log.info(f"Found worksheets - {worksheets}")
        return worksheets

    except Exception as e:
        log.error(f"Couldn't open the spreadsheet\n\n{e}")
        return

def get_worksheet(worksheetName: str) -> gspread.Worksheet | None:
    worksheets = __connect()
    if worksheetName not in worksheets:
        log.error(f"Cannot get - worksheet '{worksheetName}' does not exist")
        return
    return spreadsheet.worksheet(worksheetName)


def create_worksheet(worksheetName: str) -> gspread.Worksheet | None:
    worksheets = __connect()
    if worksheetName in worksheets:
        log.error(f"Cannot create - worksheet '{worksheetName}' already exists")
        return spreadsheet.worksheet(worksheetName)
    try:
        return spreadsheet.add_worksheet(title=worksheetName, rows=1000, cols=1000, index=len(worksheets) - 1)
    except Exception as e:
        log.error(f"Creating worksheet failed\n\n{e}")
        return

def delete_worksheet(worksheetName: str) -> bool:
    worksheets = __connect()
    if worksheetName not in worksheets:
        log.warning(f"Cannot delete - worksheet '{worksheetName}' does not exist")
        return True
    try:
        spreadsheet.del_worksheet(get_worksheet(worksheetName))
        return True
    except Exception as e:
        log.error(f"Deletion of worksheet '{worksheetName}' failed")
        return False

# https://github.com/robin900/gspread-dataframe
