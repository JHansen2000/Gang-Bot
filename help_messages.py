import discord

commands_help_embed = discord.Embed(
    title="Available Commands", 
    description="Gang Bot has a selection of slash commands for you to use!",
    color=discord.Colour.dark_blue())
commands_help_embed.add_field(
    name="/create gang",
    value="Can only be done by Administrators. \nCreates everything needed for a gang (roles, channels, roster, etc.). \nWill prompt the user for all customizations\n",
    inline=False)
commands_help_embed.add_field(
    name="/delete data",
    value="Can only be done by Administrators. \nDeletes Gang Bot's entire database, including all gangs. Cannot be undone!\n",
    inline=False)
commands_help_embed.add_field(
    name="/delete gang <gang>",
    value="Can only be done by Administrators. \nDeletes a gang and all of it's assets.\n",
    inline=False)
commands_help_embed.add_field(
    name="/change color <gang>",
    value="Can only be done by a Gang's Leader. \nChanges the primary color of a gang.\n",
    inline=False)
commands_help_embed.add_field(
    name="/change subroles <gang>",
    value="Can only be done by a Gang's Leader. \nChanges a gang's subroles.\n",
    inline=False)
commands_help_embed.add_field(
    name="/change radio <gang>",
    value="Can only be done by a Gang's High Command+. \nChanges a gang's radio information.\n",
    inline=False)
commands_help_embed.add_field(
    name="/change iban <gang>",
    value="Can be done by any Gang Member. \nChanges a member's IBAN.",
    inline=False)

leaders_help_embed = discord.Embed(
    title="**This is Your Gang!**",
    description="We've pre-configured the gang, but it is ***yours***. \nFeel free to create your own channels, modify channel permissions, or anything else you'd like!!",
    color=discord.Colour.dark_blue())
leaders_help_embed.add_field(
    name="Adding Members",
    value="You and your Command staff can add roles for **your** gang. Just do it through the normal Discord UI. \nThe bot will remove roles automatically if you're not permitted to assign them.",
    inline=False)