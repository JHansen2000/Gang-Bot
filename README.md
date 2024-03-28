## Installation Steps:
- Create .venv (via VS Code)
    - Cmd + P: ">Python: Create Environment..."
- `pip install -r requirements.txt`
- Obtain the GCloud Service Account private_key.json from Heros451 (Discord: chuckledusters)
- Share the spreadsheet with the `client_email` in private_key.json
- `python3 main.py`

## Current Task:
- Fix deleting row from bot_data

## TODO
- Create following event handlers:
  - User Nickname Change
  - Role Color Modified
  - User Role Change
    - Command role changed
    - Gang role changed
- On Gang Create (and vice versa for delete)
  - Create filetree and set permissions
  - Require leader member on creation
  - Populate sheet with default data
  - Fix color options
  - Verify that role IS a gang
- Log changes in #audit-log channel
- Auto create 'bot_data' sheet on db_health_check if it doesn't exist

## Done
- Pong a pinging user
- Identify commands from admins
- Update a remote roster (google sheets w/ pandas)