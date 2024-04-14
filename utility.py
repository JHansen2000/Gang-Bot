import pandas as pd
from discord import Guild, Role, CategoryChannel, TextChannel, Member
from help_messages import commands_help_embed, leaders_help_embed
from logger import Logger
log = Logger()

def get_role(guild: Guild, id: str) -> Role:
  role = guild.get_role(int(id))
  if not role: raise Exception("Could not get role")
  return role

def get_rid_by_name(member: Member, name: str) -> int:
  return [role.id for role in member.roles if role.name == name][0]

def get_category(guild: Guild, cid: str) -> CategoryChannel:
  category = [cat for cat in guild.categories if str(cat.id) == cid][0]
  if not category:
    raise Exception("Couldn't get category")
  return category

async def create_category(guild: Guild, role: Role) -> CategoryChannel:
  log.info(f"Creating category '{role.name}'...")
  newCategory =  await guild.create_category(role.name)
  # @everyone
  await newCategory.set_permissions(guild.default_role,
    view_channel=False,
    read_messages=False,
    read_message_history=False,
    send_messages=False,
    use_application_commands=False)

  # @role
  await newCategory.set_permissions(role,
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=True,
    connect=True,
    speak=True
    )
  return newCategory

async def create_gang_channels(guild: Guild, role: Role, subroles: list[Role], category: CategoryChannel) -> list[TextChannel]:
  log.info(f"Creating channel tree for '{role.name}'...")

  leadership = await guild.create_text_channel(
    name="leadership",
    category=category)
  await leadership.set_permissions(role, view_channel=False)
  await leadership.set_permissions(subroles[1], view_channel=False)
  await leadership.send(embed=leaders_help_embed)

  command = await guild.create_text_channel(
    name="command",
    category=category)
  await command.set_permissions(role, view_channel=False)

  announcements = await guild.create_text_channel(
    name="announcements",
    category=category)
  await announcements.set_permissions(role,
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=False)

  roster = await guild.create_text_channel(
    name="roster",
    category=category)
  await roster.set_permissions(guild.default_role,
    view_channel=True,
    read_messages=True,
    read_message_history=True)
  await roster.set_permissions(role, send_messages=False)
  await roster.set_permissions(subroles[0],
    send_messages=False,
    manage_channels=False,
    manage_permissions=False,
    manage_messages=False)
  await roster.set_permissions(subroles[1],
    send_messages=False,
    manage_messages=False)

  radio = await guild.create_text_channel(
    name="radio",
    category=category)
  await announcements.set_permissions(role,
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=False)
  await radio.set_permissions(subroles[0],
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=False,
    manage_channels=False,
    manage_permissions=False,
    manage_messages=False)
  await radio.set_permissions(subroles[1],
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=False,
    manage_messages=False)

  intel = await guild.create_text_channel(
    name="intel",
    category=category)
  await intel.set_permissions(role, view_channel=False)
  await intel.set_permissions(subroles[2],
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=True)

  await guild.create_text_channel(
    name="general",
    category=category)

  await guild.create_text_channel(
    name="off-topic",
    category=category)

  bot_commands = await guild.create_text_channel(
    name="bot-commands",
    category=category)
  await bot_commands.set_permissions(guild.default_role,
    view_channel=False,
    use_application_commands=True)
  await bot_commands.send(embed=commands_help_embed)

  await guild.create_voice_channel(
    name="VC - 1",
    category=category)

  await guild.create_voice_channel(
    name="VC - 2",
    category=category)

  vc_command = await guild.create_voice_channel(
    name="VC - Command",
    category=category)
  await vc_command.set_permissions(role, view_channel=False)

  vc_leadership = await guild.create_voice_channel(
    name="VC - Leadership",
    category=category)
  await vc_leadership.set_permissions(role, view_channel=False)
  await vc_leadership.set_permissions(subroles[1], view_channel=False)

  return [roster, radio]

async def update_gang_category(category: CategoryChannel, subroles: list[Role]) -> None:
  # @Gang Leader
  await category.set_permissions(subroles[0],
    manage_channels=True,
    manage_messages=True,
    mute_members=True,
    deafen_members=True,
    move_members=True,
    manage_permissions=True,
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=True,
    connect=True,
    speak=True)

  # @High Command
  await category.set_permissions(subroles[1],
    manage_messages=True,
    mute_members=True,
    deafen_members=True,
    move_members=True,
    view_channel=True,
    read_messages=True,
    read_message_history=True,
    send_messages=True,
    connect=True,
    speak=True)

async def delete_category(guild: Guild, cid: str) -> None:
  category = get_category(guild, cid)
  log.info(f"Deleting category '{category.name}'...")
  channels = category.channels
  for channel in channels:
    try:
      await channel.delete()
    except Exception as e:
      log.error(f"Failed to delete channel {channel.name}\n\n{e}")
      pass
  await category.delete()