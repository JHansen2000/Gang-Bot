from discord import AuditLogAction, AuditLogEntry, Client, Role
import sheets
import logger
# from utility import get_roles
log = logger.Logger()


def get_events(client: Client, db: sheets.Database) -> None:
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


                all_gangs = db.get_all_gangs(guild)
                isGangRole = True if changed_role in all_gangs else False
                if isGangRole:
                    db.update_bot(changed_role)
                    db.update_gang(changed_role.name, member, delete)
                    log.info(f"Role @{changed_role.name} {message} '{member.name}'")
                    return


                for gang in all_gangs:
                    gang_CRIDs = db.get_crids(gang)
                    if gang_CRIDs.get(str(changed_role.id)):
                        db.update_gang(gang.name, member, False)
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

                for gang in db.get_gangs(member):
                    db.update_gang(gang.name, member, False)
                log.info("Member nickname updated")

        else:
            log.warning(str(entry.action))