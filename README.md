## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- Color selection embed before final result (EMBED COLOR SHOULD CHANGE WITH INPUT)
- Create command to change subrole titles
- Create command to update radio channel

## TODO
- Make all messages rich embeds
- Log changes in #audit-log channel
- Create command to create joint categories
  - **STRETCH** Delete joint categories if one gang is deleted
- **STRETCH** Create custom tags (non-functional)
- **STRETCH** Create refresh button on gang sheets
