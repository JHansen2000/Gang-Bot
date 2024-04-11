## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- Create command to change subrole titles
- Create command to update radio channel
- Create IBAN command (roster button modal)

## TODO
- Log changes in #audit-log channel
- Create event handler on member leave
- Create event handler on member join
- Create command to create joint categories
  - **STRETCH** Delete joint categories if one gang is deleted
- **STRETCH** Create custom tags (non-functional)
- **STRETCH** Create refresh button on gang sheets
