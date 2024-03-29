from discord import CategoryChannel, Client, Guild, Member, PermissionOverwrite, Role, Colour
import logger
log = logger.Logger()

ROLES = {
  "ADMIN": 5,
  "Gang Leader" : 4,
  "High Command": 3,
  "Member": 2,
  "Hangaround": 1
}

def get_power(member: Member, roles: dict[str, int] = ROLES) -> int:
  power = 0
  for role in member.roles:
    if role.name in roles:
      role_power = roles.get(role.name)
      if role_power:
        power = max(role_power, power)
  return power

def can_execute(member: Member, required_power: int, target) -> bool:
  if not target:
    if get_power(member) >= required_power:
      log.info("User meets/exceeds required power")
      return True
    log.warning("User does not meet required power")
    return False

  print(target)

  if get_power(member) >= required_power:
    log.info("User meets/exceeds required power")
    return True
  log.warning("User does not meet required power")
  return False

async def new_role(guild: Guild, roleName: str, colorRequest: str | None) -> Role | None:

  if not colorRequest:

    color = Colour.default()
  else:
    match len(colorRequest):
      case 6:
        color = int(colorRequest.strip())
      case 7:
        color = int(colorRequest.strip()[1:])
      case _:
        color = Colour.default()

  try:
    newRole = await guild.create_role(name=roleName, color=color, hoist=True, mentionable=True)
    log.info(f"Created new role @{newRole.name}")
    return newRole
  except Exception as e:
    log.error(f"Failed to create role @{roleName}\n\n{e}")
    return

async def delete_role(role: Role) -> bool:
  try:
    await role.delete()
    log.info(f"Deleted role @{role.name}")
    return True
  except Exception as e:
    log.error(f"Failed to delete role @{role.name}\n\n{e}")
    return False

async def new_category(guild: Guild, role: Role) -> CategoryChannel | None:
  categories = [category.name for category in guild.categories]
  categories.append(role.name)
  categories.sort()

  newCategory = await guild.create_category(
    role.name,
    overwrites= {
      guild.default_role: PermissionOverwrite(read_messages=False),
      role: PermissionOverwrite(read_messages=True)
    },
    position=categories.index(role.name))

  return newCategory

async def get_category(guild: Guild, cid: str) -> CategoryChannel | None:
  category = [cat for cat in guild.categories if str(cat.id == cid)][0]
  if not category:
    log.error("Failed to find category")
    return
  return category

async def delete_category(guild: Guild, cid: str) -> bool:
  category = await get_category(guild, cid)
  if not category:
      return False

  channels = category.channels
  for channel in channels:
    try:
      await channel.delete()
    except Exception as e:
      log.error(f"Failed to delete channel {channel.name}\n\n{e}")
      pass
  await category.delete()
  return True