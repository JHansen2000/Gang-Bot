## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- Test Radio buttons/commands/create
- Radio needs to be re-initialized on bot startup

## TODO
- Log changes in #audit-log channel
- Create event handler on member leave
- Create event handler on member join
- Create command to create joint categories
- Send help messages on gang create
  - **STRETCH** Delete joint categories if one gang is deleted
- **STRETCH** Create custom tags (non-functional)
