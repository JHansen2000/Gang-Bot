## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- On Gang Create (and vice versa for delete)
    - Populate roster from database (callback from `update_gang()`)
- Color selection embed before final result (EMBED COLOR SHOULD CHANGE WITH INPUT)

## TODO
- On Gang Create (and vice versa for delete)
  - Create channel tree and set permissions
  - Require color hex on creation
- Log changes in #audit-log channel
- Disallow creation of gangs with same name as ranks
- Sort roles so gang roles are at the bottom and subroles are sorted by power (descending)
- Create command to refresh database (gang-specific)
- Create command to change subrole titles
- Create command to update radio channel
- Create command to create joint categories
  - **STRETCH** Delete joint categories if one gang is deleted
- **STRETCH** Events will automatically remove old subrole if new one is added
- **STRETCH** Create custom tags (non-functional)
