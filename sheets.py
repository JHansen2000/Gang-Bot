import os
import gspread
import logger
log = logger.Logger()

async def connect(sheetname: str) -> gspread.Worksheet | None:
    if "private_key.json" not in os.listdir("private/"):
            log.error("private_key.json not found in the private/ directory")
            return
    try:
        spreadsheet = gspread.service_account(filename="private/private_key.json")
        # Open a sheet from a spreadsheet in one go
        worksheet = spreadsheet.open(sheetname).sheet1
        return worksheet
    except Exception as e:
        log.error(f"Couldn't open the spreadsheet\n\n{e}")
        return

# https://github.com/robin900/gspread-dataframe
