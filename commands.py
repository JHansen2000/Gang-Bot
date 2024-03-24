from discord import Interaction

def get_commands(tree, guild):
    @tree.command (
        name="ping",
        description="Ping Gang Bot!",
        guild=guild,
    )
    async def ping(interaction: Interaction):
        await interaction.response.send_message("Pong!")

    @tree.command (
        name="pong",
        description="Pong Gang Bot!",
        guild=guild,
    )
    async def pong(interaction: Interaction):
        await interaction.response.send_message("Ping!")