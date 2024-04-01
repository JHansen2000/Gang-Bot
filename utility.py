from discord import CategoryChannel, Guild, Member, PermissionOverwrite, Role, Colour
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
    return True if get_power(member) >= required_power else False
  return True if get_power(member) >= required_power else False

async def new_role(guild: Guild, roleName: str, colorRequest: str | None) -> Role:
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

    newRole = await guild.create_role(name=roleName, color=color, hoist=True, mentionable=True)
    return newRole

async def new_category(guild: Guild, role: Role) -> CategoryChannel:
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

def get_category(guild: Guild, cid: str) -> CategoryChannel:
  category = [cat for cat in guild.categories if str(cat.id == cid)][0]
  if not category:
    raise Exception("Couldn't get category")
  return category

async def delete_category(guild: Guild, cid: str) -> None:
  category = get_category(guild, cid)
  channels = category.channels
  for channel in channels:
    try:
      await channel.delete()
    except Exception as e:
      log.error(f"Failed to delete channel {channel.name}\n\n{e}")
      pass
  await category.delete()

def get_role(guild: Guild, id: str) -> Role:
  role = guild.get_role(int(id))
  if not role: raise Exception("Could not get role")
  return role

def get_roles(guild: Guild) -> list[Role]:
  return [role for role in guild.roles if role.name in ROLES]