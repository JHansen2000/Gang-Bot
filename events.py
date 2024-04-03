from discord import AuditLogAction, AuditLogEntry, Client, Role
from sheets import update_data_worksheet, update_gang_worksheet, get_all_gangs
import logger
from utility import get_roles
log = logger.Logger()


def get_events(client: Client) -> None:
    # @client.event
    # async def on_member_update(before: Member, after: Member) -> None:

    @client.event
    async def on_audit_log_entry_create(entry: AuditLogEntry) -> None:
        return # TEMPORARY SKIP
        if entry.user and not entry.user.bot:
            if entry.action is AuditLogAction.member_role_update:
                # entry.user.name # Instigator
                # entry.target # Target

                guild = entry.guild
                target_id = entry._target_id
                if not target_id: raise Exception("Failed to get target_id")

                member = guild.get_member(target_id)
                if not member: raise Exception(f"Failed to get member with ID {target_id}")

                pre_roles: list[Role] = entry.before.__dict__.get('roles') # type: ignore
                post_roles: list[Role] = entry.after.__dict__.get('roles') # type: ignore
                print(pre_roles)
                print(post_roles)


                if len(pre_roles) > len(post_roles):
                    message = "removed from"
                    changed_role = pre_roles[0]
                    delete = True
                else:
                    message = "added to"
                    changed_role = post_roles[0]
                    delete = False

                isGangRole = True if changed_role in get_all_gangs(guild) else False
                isRankRole = True if changed_role in get_roles(guild) else False
                if not isGangRole and not isRankRole:
                    log.warning(f"Role @{changed_role.name} is not a key role")
                    return

                elif not isGangRole:
                    for gang in get_gangs(member):
                        update_gang_worksheet(gang.name, member, False)

                else:
                    update_data_worksheet(changed_role)
                    update_gang_worksheet(changed_role.name, member, delete)


                log.info(f"Role @{changed_role.name} {message} '{member.name}'")
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