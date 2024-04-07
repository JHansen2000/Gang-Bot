## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- On Gang Create (and vice versa for delete)
  - Create channel tree and set permissions
- Color selection embed before final result (EMBED COLOR SHOULD CHANGE WITH INPUT)

## TODO
- On Gang Create (and vice versa for delete)
  - Create channel tree and set permissions
  - Require color hex on creation
  - Populate sheet with default data
- Log changes in #audit-log channel
- Disallow creation of gangs with same name as ranks
