from discord import Member

ROLES = {
  "ADMIN": 5,
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

def get_gang(member: Member) -> str:
  return ""

def update_db(member: Member) -> None:
  temp = 1
  # Update a sheet in the database containing user information