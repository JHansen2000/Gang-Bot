import os
from dotenv import load_dotenv
from discord import Intents, Client, Guild, Object, app_commands
from commands import get_commands
from sheets import db_healthy

# Import custom logger
import logger
log = logger.Logger()

# Load TOKEN from .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    log.fatal("Unable to get DISCORD_TOKEN")
    exit()

GUILD = os.getenv('GUILD_ID')
if not GUILD:
    log.fatal("Unable to get GUILD_ID")
    exit()
GUILD = Object(id=GUILD)

# Declarations -> None
intents: Intents = Intents.default()
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)
get_commands(tree, GUILD)

@client.event
async def on_ready() -> None:
    try:
        synced = await tree.sync(guild=GUILD)
        log.info(f"Synced {len(synced)} command(s)...")
        log.info(f"{client.user} is now running")
    except Exception as e:
        log.fatal(f"Failed to start\n\n{e}\n\n")

def main() -> None:
    log.info("Running health checks...")
    if not db_healthy():
        exit()
    client.run(token=TOKEN)

if __name__ == '__main__':
    main()