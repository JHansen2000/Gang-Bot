from discord import Guild, Member, Role, Colour
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
      power = max(ROLES.get(role.name), power)
  return power

def can_execute(member: Member, required_power: int, target) -> bool:
  if not target:
    if get_power(member) >= required_power:
      log.info("User meets/exceeds required power")
      return True
    log.warn("User does not meet required power")
    return False

  print(target)

  if get_power(member) >= required_power:
    log.info("User meets/exceeds required power")
    return True
  log.warn("User does not meet required power")
  return False

def new_role(guild: Guild, roleName: str, colorRequest: str) -> Role | None:
  match len(colorRequest):
    case 6:
      color = int(colorRequest.strip())
    case 7:
      color = int(colorRequest.strip[1:])
    case _:
      color = Colour.default()

  try:
    newRole = guild.create_role(name=roleName, color=color, hoist=True, mentionable=True)
    log.info(f"Created new role @{newRole.name}")
    return newRole
  except Exception as e:
    log.error(f"Failed to create role @{roleName}\n\n{e}")
    return

def delete_role(role: Role) -> bool:
  try:
    role.delete()
    log.info(f"Deleted role @{role.name}")
    return True
  except Exception as e:
    log.error(f"Failed to delete role @{role.name}\n\n{e}")
    return False