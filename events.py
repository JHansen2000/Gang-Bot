from discord import AuditLogAction, AuditLogEntry, Client, Role
import sheets
import logger
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
        caller_id = entry.user_id
        if not caller_id: raise Exception(f"Failed to get called_id")
        caller = guild.get_member(caller_id)
        if not caller: raise Exception(f"Failed to get caller with ID {caller_id}")

        pre_roles: list[Role] = entry.before.__dict__.get('roles') # type: ignore
        post_roles: list[Role] = entry.after.__dict__.get('roles') # type: ignore

        if len(pre_roles) > len(post_roles):
          changed_role = pre_roles[0]
          delete = True
        else:
          changed_role = post_roles[0]
          delete = False

        all_gangs = db.get_all_gangs(guild)
        isSubrole = False
        isGangRole = False
        if changed_role in all_gangs:
          isGangRole = True
          gang_role = changed_role
        else:
          for gang in all_gangs:
            if changed_role in db.get_subroles(gang, guild):
              gang_role = gang
              isSubrole = True
        if not isGangRole and not isSubrole:
          log.warning(f"Role @{changed_role.name} is not a key role")
          return

        canExecute = False
        if sheets.isAdmin(caller):
          canExecute = True
        elif isGangRole:
          canExecute = db.can_execute(caller, 3, changed_role, isEvent=False)
          crids = db.get_crids(changed_role)
          if db.get_power(caller, crids) <= db.get_power(member, crids):
            canExecute = False
        else:
          canExecute = db.can_execute(caller, 3, gang_role, isEvent=True) # type: ignore
          crids = db.get_crids(gang_role) # type: ignore
          if db.get_power(caller, crids) <= db.get_power(member, crids, opt_role=changed_role):
            canExecute = False

        if not canExecute:
          if delete:
            await member.add_roles(changed_role)
          else:
            await member.remove_roles(changed_role)
          return

        dataModified = False
        gangModified = False
        if delete:
          if isGangRole:
            log.info(f"@{caller.name} is removing gang @{changed_role.name} from @{member.name}")
            for subrole in db.get_subroles(changed_role, guild):
              await member.remove_roles(subrole)
            dataModified = True
            gangModified = True

          else:
            log.info(f"@{caller.name} is removing subrole @{changed_role.name} from @{member.name}")
            await member.add_roles(db.get_subroles(gang_role, guild)[-1])
            gangModified = True


        else:
          if isGangRole:
            log.info(f"@{caller.name} is adding gang @{changed_role.name} to @{member.name}")
            await member.add_roles(db.get_subroles(changed_role, guild)[-1])
            dataModified = True
            gangModified = True

          else:
            log.info(f"@{caller.name} is adding subrole @{changed_role.name} to @{member.name}")
            if gang_role not in member.roles:
              await member.add_roles(gang_role)
              dataModified = True
            subrole = db.get_subrole(gang_role, member, exclude=changed_role)
            if subrole:
              await member.remove_roles(subrole)
            gangModified = True

        if dataModified:
          db.update_bot(gang_role)
        if gangModified:
          db.update_gang(gang_role.name, member, delete)
          channel_id = sheets.get_df_at(db.bot_df, gang_role.id, "RID", "RoCID")
          roster = guild.get_channel(int(channel_id))
          await sheets.update_roster(roster, db.get_gang_df(gang_role.name)) # type: ignore

        return

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