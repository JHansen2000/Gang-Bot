from discord import AuditLogAction, AuditLogEntry, Client, Role
import sheets
import logger
# from utility import get_roles
log = logger.Logger()


def get_events(client: Client, db: sheets.Database) -> None:
    # @client.event
    # async def on_member_update(before: Member, after: Member) -> None:

    # Add listener for role deletion logging
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

                caller_id = entry.user_id
                if not caller_id: raise Exception(f"Failed to get called_id")
                caller = guild.get_member(caller_id)
                if not caller: raise Exception(f"Failed to get caller with ID {caller_id}")

                all_gangs = db.get_all_gangs(guild)
                isGangRole = False
                gang_role = None
                for gang in all_gangs:
                    if gang == changed_role:
                        isGangRole = True
                        break
                    if changed_role in db.get_subroles(gang, guild):
                        gang_role = gang
                        break

                if not isGangRole and not gang_role:
                    log.warning(f"Role @{changed_role.name} is not a key role")
                    return

                if isGangRole: 
                    canExecute = db.can_execute(caller, changed_role, 3, isEvent=False)
                    crids = db.get_crids(changed_role)
                    if db.get_power(caller, crids) <= db.get_power(member, crids):
                        canExecute = False
                else:
                    canExecute = db.can_execute(caller, gang_role, 3, isEvent=True) # type: ignore
                    crids = db.get_crids(gang_role) # type: ignore
                    if db.get_power(caller, crids) <= db.get_power(member, crids, opt_role=changed_role): #TEST
                        canExecute = False
                # Above fails BECAUSE check is done after role is removed
                # Need to add role back ONLY if a *subrole* has been *removed*

                if not canExecute:
                    if delete:
                        await member.add_roles(changed_role)
                    else:
                        await member.remove_roles(changed_role)
                    return


                if isGangRole:
                    subrole = db.get_subrole(changed_role, member)
                    db.update_bot(changed_role)
                    db.update_gang(changed_role.name, member, delete)
                    await member.remove_roles(subrole)
                    log.info(f"Role @{changed_role.name} {message} '{member.name}'")
                    return

                for gang in all_gangs:
                    gang_CRIDs = db.get_crids(gang)
                    if gang_CRIDs.get(str(changed_role.id)):
                        if not isGangRole:
                            await member.add_roles(gang)
                            db.update_bot(gang)
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
            if entry.action is AuditLogAction.role_delete:
                log.info(f"Bot deleted role: {entry.changes}")
            log.warning(str(entry.action))