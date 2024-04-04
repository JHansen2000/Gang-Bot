from discord import CategoryChannel, Guild, Member, PermissionOverwrite, Role, Colour
import logger
log = logger.Logger()

async def new_role(guild: Guild, roleName: str, hoisted: bool = True) -> Role:
    newRole = await guild.create_role(name=roleName, hoist=hoisted, mentionable=True)
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

# def get_roles(guild: Guild) -> list[Role]:
#   return [role for role in guild.roles if role.name in ROLES]

async def create_subroles(guild: Guild, role: Role, rmap: dict[str, str]) -> dict[str, str]:
  newMap: dict[str, str] = {}

  for key, value in rmap.items():
    newName = f"{role.name} - {value}"
    power = rmap.get(key)

    if not power:
      raise Exception(f"Could not find {key} in role map")

    newRole = await new_role(guild, newName, hoisted=False)
    newMap[str(newRole.id)] = power
  return newMap