import os
from dotenv import load_dotenv
from discord import Intents, Client, Object, app_commands
from commands import get_commands
from sheets import Database
from events import get_events
from logger import Logger
log = Logger()

log.info("Loading environment...")
load_dotenv()
DISCORD_TOKEN=os.getenv('DISCORD_TOKEN')
GUILD_ID=os.getenv('GUILD_ID')
SPREADSHEET_ID=os.getenv("SPREADSHEET_ID")
ADMIN_ID=os.getenv("ADMIN_ID")
if not DISCORD_TOKEN:
  log.error("Failed to get DISCORD_TOKEN")
  exit()
if not GUILD_ID:
  log.error("Failed to get GUILD_ID")
  exit()
if not SPREADSHEET_ID:
  log.error("Failed to get SPREADSHEET_ID")
  exit()
if not ADMIN_ID:
  log.error("Failed to get ADMIN_ID")
  exit()
if "private_key.json" not in os.listdir("private/"):
  log.error("private_key.json not found in the private/ directory")
  exit()

log.info("Initializing client...")
intents: Intents = Intents.default()
intents.members = True
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)

log.info("Initializing command tree...")
global_db = Database(SPREADSHEET_ID)
get_commands(tree, global_db, guild=Object(int(GUILD_ID)))
get_events(client, global_db)

@client.event
async def on_ready() -> None:
    try:
        guild = await client.fetch_guild(int(GUILD_ID))
        synced = await tree.sync(guild=guild)
        log.info(f"Synced {len(synced)} command(s)...")
        log.info(f"{client.user} is now running")
        await global_db.init_gang_rosters(guild)
    except Exception as e:
        log.fatal(f"Failed to start\n\n{e}\n\n")

def main() -> None:
  try:
    client.run(token=DISCORD_TOKEN)
  except Exception as e:
    raise e

if __name__ == '__main__':
  main()