from discord import Client, Guild, Member, Role, Colour
import logger
log = logger.Logger()

ROLES = {
  "ADMIN": 6,
  "Gang Leader" : 5,
  "High Command": 4,
  "Low Command": 3,
  "Member": 2,
  "Hangaround": 1
}

def get_power(member: Member) -> int:
  power = 0
  for role in member.roles:
    if role.name in ROLES:
      role_power = ROLES.get(role.name)
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
