from discord import AuditLogAction, AuditLogEntry, Client, Role, TextChannel
import sheets
import logger
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
                caller_id = entry.user_id
                if not caller_id: raise Exception(f"Failed to get called_id")
                caller = guild.get_member(caller_id)
                if not caller: raise Exception(f"Failed to get caller with ID {caller_id}")

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

                log.info(f"CHANGED_ROLE: {changed_role.name}")

                all_gangs = db.get_all_gangs(guild)
                isSubrole = False
                isGangRole = True
                if changed_role not in all_gangs:
                  isGangRole = False
                  gang_role = None
                  for gang in all_gangs:
                      if changed_role in db.get_subroles(gang, guild):
                          gang_role = gang
                          isSubrole = True
                          break
                  if not gang_role:
                    log.warning(f"Role @{changed_role.name} is not a key role")
                    return

                try:
                    canExecute = False
                    if sheets.isAdmin(caller):
                        canExecute = True
                    elif isGangRole:
                        canExecute = db.can_execute(caller, 3, changed_role, isEvent=False)
                        crids = db.get_crids(changed_role)
                        if db.get_power(caller, crids) <= db.get_power(member, crids):
                            canExecute = False
                    else:
                        canExecute = db.can_execute(caller, gang_role, 3, isEvent=True) # type: ignore
                        crids = db.get_crids(gang_role) # type: ignore
                        if db.get_power(caller, crids) <= db.get_power(member, crids, opt_role=changed_role):
                            canExecute = False

                    if not canExecute:
                        if delete:
                            await member.add_roles(changed_role)
                        else:
                            await member.remove_roles(changed_role)
                        return

                    if isGangRole:

                        subrole = db.get_subrole(changed_role, member)
                        if not subrole:
                            log.info("subrole = None")
                            log.info(f"Adding hangaround role")
                            await member.add_roles(db.get_subroles(changed_role, guild)[-1])
                        else:
                            log.info(f"subrole = {subrole.name}")
                            log.info(f"Removing role {subrole.name}")
                            await member.remove_roles(subrole)

                        db.update_bot(changed_role)
                        db.update_gang(changed_role.name, member, delete)
                        channel_id = sheets.get_df_at(db.bot_df, changed_role.id, "RID", "RoCID")
                        roster = guild.get_channel(int(channel_id))
                        if not roster: raise Exception("Could not update roster channel")
                        await sheets.update_roster(roster, db.get_gang_df(changed_role.name)) # type: ignore

                    else:
                        log.info("isGangRole = False")
                        subrole = db.get_subrole(gang, member, changed_role)
                        if subrole and isSubrole:
                            log.info(f"subrole = {subrole.name}, isSubrole = True")
                            log.info(f"Removing role {subrole.name}")
                            await member.remove_roles(subrole)
                        elif isSubrole:
                            log.info("subrole = None, isSubrole = True")
                            log.info(f"Adding hangaround role")
                            await member.add_roles(db.get_subroles(gang, guild)[-1])

                        log.info(f"Adding role {gang.name}")
                        await member.add_roles(gang)
                        db.update_bot(gang)
                        db.update_gang(gang.name, member, False)
                        channel_id = sheets.get_df_at(db.bot_df, gang.id, "RID", "RoCID")
                        roster = guild.get_channel(int(channel_id))
                        if not roster: raise Exception("Could not update roster channel")
                        await sheets.update_roster(roster, db.get_gang_df(gang.name)) # type: ignore

                    log.info(f"Role @{changed_role.name} {message} '{member.name}'")
                    return

                except Exception as e:
                        if not canExecute:
                            if delete:
                                await member.add_roles(changed_role)
                            else:
                                await member.remove_roles(changed_role)
                            return
                        raise e

            elif entry.action is AuditLogAction.member_update:
                guild = entry.guild

                target_id = entry._target_id
                if not target_id: raise Exception("Failed to get target_id")

                member = guild.get_member(target_id)
                if not member: raise Exception(f"Failed to get member with ID {target_id}")

                for gang in db.get_gangs(member):
                    db.update_gang(gang.name, member, False)
                    channel_id = sheets.get_df_at(db.bot_df, gang.id, "RID", "RoCID")
                    roster = guild.get_channel(int(channel_id))
                    await sheets.update_roster(roster, db.get_gang_df(gang.name)) # type: ignore
                log.info("Member nickname updated")

        else:
            if entry.action is AuditLogAction.role_delete:
                log.info(f"Bot deleted role: {entry.changes.before.name}")
            # log.warning(str(entry.action))