import os
from dotenv import load_dotenv
from discord import Intents, Client, Object, app_commands
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
log.info(f"Loaded DISCORD_TOKEN - {TOKEN}")

guild_id = os.getenv('GUILD_ID')
if not guild_id:
    log.fatal("Unable to get GUILD_ID")
    exit()
guild_id = int(guild_id)
log.info(f"Loaded GUILD_ID - {guild_id}")
guild = Object(guild_id)

# Declarations -> None
intents: Intents = Intents.default()
intents.members = True
client: Client = Client(intents=intents)
tree = app_commands.CommandTree(client)
get_commands(tree, guild)


@client.event
async def on_ready() -> None:
    try:
        guild = await client.fetch_guild(guild_id)
        synced = await tree.sync(guild=guild)
        log.info(f"Synced {len(synced)} command(s)...")
        log.info(f"{client.user} is now running")
    except Exception as e:
        log.fatal(f"Failed to start\n\n{e}\n\n")

def main() -> None:
    try:
        log.info("Running health checks...")
        db_healthy()
        client.run(token=TOKEN)
    except Exception as e:
        raise e

if __name__ == '__main__':
    main()