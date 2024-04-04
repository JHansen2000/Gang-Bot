from discord import Guild, Role, PermissionOverwrite, CategoryChannel

def get_role(guild: Guild, id: str) -> Role:
  role = guild.get_role(int(id))
  if not role: raise Exception("Could not get role")
  return role

async def create_role(guild: Guild, roleName: str, hoisted: bool = True) -> Role:
  newRole = await guild.create_role(name=roleName, hoist=hoisted, mentionable=True)
  return newRole

async def create_category(guild: Guild, role: Role) -> CategoryChannel:
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

async def create_subroles(guild: Guild, role: Role, rmap: dict[str, str]) -> dict[str, str]:
  newMap: dict[str, str] = {}

  for key, value in rmap.items():
    newName = f"{role.name} - {value}"
    power = rmap.get(key)

    if not power:
      raise Exception(f"Could not find {key} in role map")

    newRole = await create_role(guild, newName, hoisted=False)
    newMap[str(newRole.id)] = power
  return newMap
