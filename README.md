## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- On Gang Create (and vice versa for delete)
  - Populate sheet with headers only
  - Create channel tree and set permissions
- Update Bot Data command (role | none, category | none, etc.)

## TODO
- Create following event handlers:
  - User Nickname Change
  - Role Color Modified
- On Gang Create (and vice versa for delete)
  - Create channel tree and set permissions
  - Require color hex on creation
  - Optional leader
  - Populate sheet with default data
- Log changes in #audit-log channel
- Map community rank to user-defined rank structure
- Promote member
- Demote member
- Kick member


## Done
- Pong a pinging user
- Identify commands from admins
- Auto create 'bot_data' sheet on db_health_check if it doesn't exist
- Update a remote roster (google sheets w/ pandas)
- On Gang Create (and vice versa for delete)
  - Verify that role IS a gang