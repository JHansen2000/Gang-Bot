import os
from dotenv import load_dotenv
from discord import Interaction, Object

# Import custom logger
import logger
log = logger.Logger()

# Load TOKEN from .env
load_dotenv()
GUILD = os.getenv('GUILD_ID')
if not GUILD:
    log.fatal("Unable to get GUILD_ID")
    exit()
GUILD = Object(id=GUILD)

def get_commands(tree):
    @tree.command (
        name="ping",
        description="Ping Gang Bot!",
        guild=GUILD,
    )
    async def ping(interaction: Interaction):
        await interaction.response.send_message("Pong!")

    @tree.command (
        name="pong",
        description="Pong Gang Bot!",
        guild=GUILD,
    )
    async def pong(interaction: Interaction):
        await interaction.response.send_message("Ping!")