from discord import AuditLogAction, AuditLogEntry, Client, Role
from sheets import get_CRIDs_dict, update_data_worksheet, update_gang_worksheet, get_all_gangs, get_gangs
import logger
# from utility import get_roles
log = logger.Logger()


def get_events(client: Client) -> None:
    # @client.event
    # async def on_member_update(before: Member, after: Member) -> None:

    @client.event
    async def on_audit_log_entry_create(entry: AuditLogEntry) -> None:
        if entry.user and not entry.user.bot:
            if entry.action is AuditLogAction.member_role_update:
                guild = entry.guild
                target_id = entry._target_id
                if not target_id: raise Exception("Failed to get target_id")

                member = guild.get_member(target_id)
                if not member: raise Exception(f"Failed to get member with ID {target_id}")

                pre_roles: list[Role] = entry.before.__dict__.get('roles') # type: ignore
                post_roles: list[Role] = entry.after.__dict__.get('roles') # type: ignore

                if len(pre_roles) > len(post_roles):
                    message = "removed from"
                    changed_role = pre_roles[0]
                    delete = True
                else:
                    message = "added to"
                    changed_role = post_roles[0]
                    delete = False


                all_gangs = get_all_gangs(guild)
                isGangRole = True if changed_role in all_gangs else False
                if isGangRole:
                    update_data_worksheet(changed_role)
                    update_gang_worksheet(changed_role.name, member, delete)
                    log.info(f"Role @{changed_role.name} {message} '{member.name}'")
                    return


                for gang in all_gangs:
                    gang_CRIDs = get_CRIDs_dict(gang)
                    if gang_CRIDs.get(str(changed_role.id)):
                        update_gang_worksheet(gang.name, member, False)
                        log.info(f"Role @{changed_role.name} {message} '{member.name}'")
                        return

                log.warning(f"Role @{changed_role.name} is not a key role")
                return

            elif entry.action is AuditLogAction.member_update:
                guild = entry.guild

                target_id = entry._target_id
                if not target_id: raise Exception("Failed to get target_id")

                member = guild.get_member(target_id)
                if not member: raise Exception(f"Failed to get member with ID {target_id}")

                for gang in get_gangs(member):
                    update_gang_worksheet(gang.name, member, False)
                log.info("Member nickname updated")

        else:
            log.warning(str(entry.action))