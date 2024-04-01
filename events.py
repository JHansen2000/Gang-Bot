from discord import Client, Member
from sheets import get_gangs, update_data_worksheet, update_gang_worksheet
import logger
from utility import get_category
log = logger.Logger()


def get_events(client: Client) -> None:
    @client.event
    async def on_member_update(before: Member, after: Member) -> None: 

        # Member's roles were updated
        if before.roles != after.roles:  
            if before.roles < after.roles:
                removed = [role for role in before.roles if role not in set(after.roles)][0]
                update_gang_worksheet(removed.name, after, True)
                update_data_worksheet(removed)
                log.info(f"Role @{removed.name} removed from '{before.name}'")
            else:
                added = [role for role in after.roles if role not in set(before.roles)][0]
                update_gang_worksheet(added.name, after, False)
                update_data_worksheet(added)
                log.info(f"Role @{added} added to '{before.name}'")
            return

        # Member's name was updated 
        if before.nick != after.nick:
            for gang in get_gangs(after):
                update_gang_worksheet(gang.name, after, False)
            log.info("Member nickname updated")

        