from discord import Guild, Role, PermissionOverwrite, CategoryChannel
from logger import Logger
log = Logger()

def get_role(guild: Guild, id: str) -> Role:
  role = guild.get_role(int(id))
  if not role: raise Exception("Could not get role")
  return role

async def create_role(guild: Guild, roleName: str, hoisted: bool = True) -> Role:
  log.info(f"Creating role @{roleName}...")
  newRole = await guild.create_role(name=roleName, hoist=hoisted, mentionable=True)
  return newRole

async def create_category(guild: Guild, role: Role) -> CategoryChannel:
  log.info(f"Creating category '{role.name}'...")
  newCategory = await guild.create_category(
    role.name,
    overwrites= {
      guild.default_role: PermissionOverwrite(read_messages=False),
      role: PermissionOverwrite(read_messages=True)
    })
  return newCategory

async def create_subroles(guild: Guild, role: Role, rmap: dict[str, int]) -> dict[str, int]:
  newMap: dict[str, int] = {}

  for key, value in rmap.items():
    newName = f"{role.name} - {key}"
    power = value

    newRole = await create_role(guild, newName, hoisted=False)
    newMap[str(newRole.id)] = power
  return newMap

def get_category(guild: Guild, cid: str) -> CategoryChannel:
  category = [cat for cat in guild.categories if str(cat.id == cid)][0]
  if not category:
    raise Exception("Couldn't get category")
  return category

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