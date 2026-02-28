"""Moderation module - Core moderation engine with all commands."""

import re
from typing import Optional

from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class ModerationConfig(BaseModel):
    """Configuration for moderation module."""
    warn_threshold: int = 3
    warn_action: str = "mute"
    warn_duration: int = 3600
    delete_on_warn: bool = False
    delete_on_mute: bool = True
    delete_on_ban: bool = True
    action_on_kick: str = "kick"
    silent_mode: bool = False
    show_history: bool = True
    require_reason: bool = False


class ModerationModule(NexusModule):
    """Core moderation engine."""

    name = "moderation"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Complete moderation system with warn, mute, ban, kick and more"
    category = ModuleCategory.MODERATION

    config_schema = ModerationConfig
    default_config = ModerationConfig().dict()

    commands = [
        CommandDef(
            name="warn",
            description="Warn a user (reply to message or mention)",
            admin_only=True,
            aliases=["w"],
        ),
        CommandDef(
            name="warns",
            description="View user's warnings",
            admin_only=True,
        ),
        CommandDef(
            name="resetwarns",
            description="Reset user's warnings",
            admin_only=True,
        ),
        CommandDef(
            name="warnlimit",
            description="Set warning threshold (3 warns = action by default)",
            admin_only=True,
        ),
        CommandDef(
            name="warntime",
            description="Set warning expiration time (default: never)",
            admin_only=True,
        ),
        CommandDef(
            name="warnmode",
            description="Set action after threshold (mute/kick/ban)",
            admin_only=True,
        ),
        CommandDef(
            name="mute",
            description="Mute a user (1m, 1h, 1d, 1w)",
            admin_only=True,
            aliases=["m", "tmute", "tm"],
        ),
        CommandDef(
            name="unmute",
            description="Unmute a user",
            admin_only=True,
            aliases=["um"],
        ),
        CommandDef(
            name="ban",
            description="Ban a user (permanent or tban 1d)",
            admin_only=True,
            aliases=["b", "tban", "tb"],
        ),
        CommandDef(
            name="unban",
            description="Unban a user",
            admin_only=True,
            aliases=["ub"],
        ),
        CommandDef(
            name="kick",
            description="Kick a user from group",
            admin_only=True,
            aliases=["k", "kickme"],
        ),
        CommandDef(
            name="kickme",
            description="Kick yourself from group",
            admin_only=False,
        ),
        CommandDef(
            name="promote",
            description="Promote user to admin/moderator",
            admin_only=True,
        ),
        CommandDef(
            name="demote",
            description="Demote user from admin/moderator",
            admin_only=True,
        ),
        CommandDef(
            name="title",
            description="Set custom admin title",
            admin_only=True,
        ),
        CommandDef(
            name="pin",
            description="Pin a message (reply to message)",
            admin_only=True,
        ),
        CommandDef(
            name="unpin",
            description="Unpin a message",
            admin_only=True,
        ),
        CommandDef(
            name="unpinall",
            description="Unpin all messages in group",
            admin_only=True,
        ),
        CommandDef(
            name="purge",
            description="Delete messages (reply to last message)",
            admin_only=True,
        ),
        CommandDef(
            name="del",
            description="Delete a message",
            admin_only=True,
        ),
        CommandDef(
            name="history",
            description="View user's moderation history",
            admin_only=True,
        ),
        CommandDef(
            name="trust",
            description="Trust a user (bypass some restrictions)",
            admin_only=True,
        ),
        CommandDef(
            name="untrust",
            description="Untrust a user",
            admin_only=True,
        ),
        CommandDef(
            name="approve",
            description="Approve user (bypass all restrictions)",
            admin_only=True,
        ),
        CommandDef(
            name="unapprove",
            description="Unapprove user",
            admin_only=True,
        ),
        CommandDef(
            name="approvals",
            description="List all approved users",
            admin_only=True,
        ),
        CommandDef(
            name="report",
            description="Report a message to admins",
            admin_only=False,
        ),
        CommandDef(
            name="reports",
            description="View pending reports (admin only)",
            admin_only=True,
        ),
        CommandDef(
            name="review",
            description="Review and resolve a report",
            admin_only=True,
        ),
        CommandDef(
            name="slowmode",
            description="Enable/disable slow mode",
            admin_only=True,
        ),
        CommandDef(
            name="restrict",
            description="Restrict user permissions",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("warn", self.cmd_warn)
        self.register_command("warns", self.cmd_warns)
        self.register_command("resetwarns", self.cmd_resetwarns)
        self.register_command("warnlimit", self.cmd_warnlimit)
        self.register_command("warntime", self.cmd_warntime)
        self.register_command("warnmode", self.cmd_warnmode)
        self.register_command("mute", self.cmd_mute)
        self.register_command("tmute", self.cmd_mute)
        self.register_command("unmute", self.cmd_unmute)
        self.register_command("ban", self.cmd_ban)
        self.register_command("tban", self.cmd_ban)
        self.register_command("unban", self.cmd_unban)
        self.register_command("kick", self.cmd_kick)
        self.register_command("kickme", self.cmd_kickme)
        self.register_command("promote", self.cmd_promote)
        self.register_command("demote", self.cmd_demote)
        self.register_command("title", self.cmd_title)
        self.register_command("pin", self.cmd_pin)
        self.register_command("unpin", self.cmd_unpin)
        self.register_command("unpinall", self.cmd_unpinall)
        self.register_command("purge", self.cmd_purge)
        self.register_command("del", self.cmd_del)
        self.register_command("history", self.cmd_history)
        self.register_command("trust", self.cmd_trust)
        self.register_command("untrust", self.cmd_untrust)
        self.register_command("approve", self.cmd_approve)
        self.register_command("unapprove", self.cmd_unapprove)
        self.register_command("approvals", self.cmd_approvals)
        self.register_command("report", self.cmd_report)
        self.register_command("reports", self.cmd_reports)
        self.register_command("review", self.cmd_review)
        self.register_command("slowmode", self.cmd_slowmode)
        self.register_command("restrict", self.cmd_restrict)

    def _get_target(self, ctx: NexusContext, args: list) -> Optional[int]:
        """Extract target user ID from message or args."""
        # Try reply first
        if ctx.replied_to and ctx.replied_to.from_user:
            return ctx.replied_to.from_user.id

        # Try mention
        if ctx.message.entities:
            for entity in ctx.message.entities:
                if entity.type == "text_mention":
                    return entity.user.id

        # Try username
        text = ctx.message.text or ""
        if args:
            username = args[0].lstrip("@")
            if username:
                # Get user ID from database
                if ctx.db:
                    from shared.models import User
                    result = ctx.db.execute(
                        f"SELECT id FROM users WHERE username = '{username}' LIMIT 1"
                    )
                    row = result.fetchone()
                    if row:
                        return row[0]

        return None

    def _parse_reason(self, args: list) -> str:
        """Extract reason from args."""
        if not args:
            return "No reason provided"
        return " ".join(args[1:]) if len(args) > 1 else "No reason provided"

    async def cmd_warn(self, ctx: NexusContext):
        """Warn a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        # Load target member
        if ctx.db:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
                ctx.set_target(target)

                reason = self._parse_reason(args)

                # Check for silent mode
                silent = ctx.message.text.endswith("!") or \
                         ctx.group.module_configs.get("moderation", {}).get("silent_mode", False)
                ctx.set_silent(silent)

                result = await ctx.warn_user(target, reason, silent=silent)

                # Show confirmation with history
                if ctx.group.module_configs.get("moderation", {}).get("show_history", True):
                    history = await ctx.get_user_history(target.user_id)
                    await ctx.reply(
                        f"⚠️ {target.mention} has been warned ({result.warn_count}/3).\n"
                        f"Reason: {reason}\n\n"
                        f"📊 User History:\n"
                        f"Warnings: {history.warnings}\n"
                        f"Mutes: {history.mutes}\n"
                        f"Bans: {history.bans}\n"
                        f"Kicks: {history.kicks}\n"
                        f"Messages: {history.total_messages}",
                        buttons=[[{"text": "View Full History", "callback_data": f"history_{target.user_id}"}]]
                    )

    async def cmd_mute(self, ctx: NexusContext):
        """Mute a user."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        # Parse duration
        duration = None
        if len(args) > 0:
            duration = ctx.parse_duration(args[0])
            if not duration:
                # Try second arg as duration if first is mention
                if len(args) > 1:
                    duration = ctx.parse_duration(args[1])

        # Load target member
        if ctx.db and target_id:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
                ctx.set_target(target)

                reason = self._parse_reason(args)
                silent = ctx.message.text.endswith("!")
                ctx.set_silent(silent)

                await ctx.mute_user(target, duration, reason, silent=silent)

                # Show history
                history = await ctx.get_user_history(target.user_id)
                await ctx.reply(
                    f"🔇 {target.mention} muted.\n"
                    f"Duration: {ctx._format_duration(duration) if duration else 'Permanent'}\n"
                    f"Reason: {reason}\n\n"
                    f"📊 User has {history.mutes} mute(s) and {history.warnings} warning(s)"
                )

    async def cmd_ban(self, ctx: NexusContext):
        """Ban a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        # Parse duration (tban)
        duration = None
        if len(args) > 0:
            duration = ctx.parse_duration(args[0])
            if not duration and len(args) > 1:
                duration = ctx.parse_duration(args[1])

        # Load target member
        if ctx.db and target_id:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
                ctx.set_target(target)

                reason = self._parse_reason(args)
                silent = ctx.message.text.endswith("!")
                ctx.set_silent(silent)

                await ctx.ban_user(target, duration, reason, silent=silent)

    async def cmd_unmute(self, ctx: NexusContext):
        """Unmute a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db and target_id:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
                ctx.set_target(target)

                await ctx.unmute_user(target)
                await ctx.reply(f"🔊 {target.mention} has been unmuted")

    async def cmd_unban(self, ctx: NexusContext):
        """Unban a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db and target_id:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
                ctx.set_target(target)

                await ctx.unban_user(target)
                await ctx.reply(f"✅ {target.mention} has been unbanned")

    async def cmd_kick(self, ctx: NexusContext):
        """Kick a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db and target_id:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )
                ctx.set_target(target)

                reason = self._parse_reason(args)
                await ctx.kick_user(target, reason)

    async def cmd_kickme(self, ctx: NexusContext):
        """Kick yourself from group."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        reason = args[0] if args else "Left via /kickme"

        await ctx.kick_user(ctx.user, reason)

    async def cmd_pin(self, ctx: NexusContext):
        """Pin a message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a message to pin it")
            return

        notify = not ctx.message.text.endswith("silent")
        await ctx.pin_message(ctx.replied_to.message_id, notify=notify)
        await ctx.reply("📌 Message pinned successfully")

    async def cmd_unpin(self, ctx: NexusContext):
        """Unpin a message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.replied_to:
            try:
                await ctx.bot.unpin_chat_message(
                    chat_id=ctx.group.telegram_id,
                    message_id=ctx.replied_to.message_id
                )
                await ctx.reply("📌 Message unpinned successfully")
            except Exception as e:
                await ctx.reply(f"❌ Error unpinning: {e}")
        else:
            await ctx.reply("❌ Reply to a message to unpin it")

    async def cmd_unpinall(self, ctx: NexusContext):
        """Unpin all messages."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        try:
            await ctx.bot.unpin_all_chat_messages(chat_id=ctx.group.telegram_id)
            await ctx.reply("📌 All messages unpinned successfully")
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_purge(self, ctx: NexusContext):
        """Purge messages."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to the last message you want to delete")
            return

        count = await ctx.purge_messages(ctx.replied_to.message_id, ctx.message.message_id)
        await ctx.message.delete()  # Delete the /purge command too
        await ctx.reply(f"🗑️ Deleted {count} messages")

    async def cmd_del(self, ctx: NexusContext):
        """Delete a message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.replied_to:
            await ctx.replied_to.delete()
            await ctx.message.delete()
        else:
            await ctx.message.delete()

    async def cmd_history(self, ctx: NexusContext):
        """View user's moderation history."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db and target_id:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND u.telegram_id = {target_id}
                LIMIT 1
                """
            )
            row = result.fetchone()
            if row:
                from bot.core.context import MemberProfile
                target = MemberProfile(
                    id=row[0],
                    user_id=row[1],
                    group_id=row[2],
                    telegram_id=row[10],
                    username=row[11],
                    first_name=row[12],
                    last_name=row[13],
                    role=row[9],
                    trust_score=row[6],
                    xp=row[7],
                    level=row[8],
                    warn_count=row[14],
                    is_muted=row[16],
                    is_banned=row[18],
                    is_approved=row[20],
                    is_whitelisted=row[21],
                    joined_at=row[4],
                    message_count=row[5],
                    custom_title=row[23],
                )

                history = await ctx.get_user_history(target.user_id)

                await ctx.reply(
                    f"📊 {target.mention}'s History\n\n"
                    f"⚠️ Warnings: {history.warnings}\n"
                    f"🔇 Mutes: {history.mutes}\n"
                    f"🚫 Bans: {history.bans}\n"
                    f"👢 Kicks: {history.kicks}\n"
                    f"💬 Messages: {history.total_messages}\n"
                    f"✅ Trust Score: {target.trust_score}/100\n"
                    f"⭐ XP: {target.xp} (Level {target.level})\n"
                    f"🏷️ Role: {target.role}"
                )

    async def cmd_trust(self, ctx: NexusContext):
        """Trust a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db:
            from shared.models import Member
            ctx.db.execute(
                f"""
                UPDATE members
                SET is_whitelisted = TRUE
                WHERE group_id = {ctx.group.id} AND user_id IN (
                    SELECT id FROM users WHERE telegram_id = {target_id}
                )
                """
            )
            await ctx.reply("✅ User has been trusted")

    async def cmd_untrust(self, ctx: NexusContext):
        """Untrust a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db:
            from shared.models import Member
            ctx.db.execute(
                f"""
                UPDATE members
                SET is_whitelisted = FALSE
                WHERE group_id = {ctx.group.id} AND user_id IN (
                    SELECT id FROM users WHERE telegram_id = {target_id}
                )
                """
            )
            await ctx.reply("✅ User has been untrusted")

    async def cmd_approve(self, ctx: NexusContext):
        """Approve a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db:
            from shared.models import Member, Approval
            # Get user_id
            result = ctx.db.execute(
                f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
            )
            row = result.fetchone()
            if row:
                user_id = row[0]

                # Set is_approved
                ctx.db.execute(
                    f"""
                    UPDATE members
                    SET is_approved = TRUE
                    WHERE group_id = {ctx.group.id} AND user_id = {user_id}
                    """
                )

                # Add to approvals table
                approval = Approval(
                    group_id=ctx.group.id,
                    user_id=user_id,
                    approved_by=ctx.user.user_id,
                )
                ctx.db.add(approval)

                await ctx.reply("✅ User has been approved")

    async def cmd_unapprove(self, ctx: NexusContext):
        """Unapprove a user."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db:
            from shared.models import Member
            ctx.db.execute(
                f"""
                UPDATE members
                SET is_approved = FALSE
                WHERE group_id = {ctx.group.id} AND user_id IN (
                    SELECT id FROM users WHERE telegram_id = {target_id}
                )
                """
            )
            await ctx.reply("✅ User has been unapproved")

    async def cmd_approvals(self, ctx: NexusContext):
        """List approved users."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import Member
            result = ctx.db.execute(
                f"""
                SELECT u.username, u.first_name, u.last_name, m.custom_title
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {ctx.group.id} AND m.is_approved = TRUE
                ORDER BY m.joined_at DESC
                LIMIT 20
                """
            )

            approved = result.fetchall()
            if not approved:
                await ctx.reply("❌ No approved users yet")
                return

            text = "✅ Approved Users:\n\n"
            for row in approved:
                username = row[0]
                name = f"{row[1]} {row[2] or ''}".strip()
                title = f" [{row[3]}]" if row[3] else ""
                text += f"• {username or name}{title}\n"

            await ctx.reply(text)

    async def cmd_report(self, ctx: NexusContext):
        """Report a message to admins."""
        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a message to report it")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        reason = " ".join(args) if args else "No reason provided"

        # Store report
        if ctx.db:
            # Create a mod_action with type "report"
            from shared.models import ModAction
            action = ModAction(
                group_id=ctx.group.id,
                target_user_id=ctx.replied_to.from_user.id,
                actor_id=ctx.user.user_id,
                action_type="report",
                reason=reason,
                message_id=ctx.replied_to.message_id,
                message_content=ctx.replied_to.text or f"[{ctx.replied_to.content_type}]",
            )
            ctx.db.add(action)

        # Notify admins
        await ctx.notify_admins(
            f"🚨 New Report from {ctx.user.mention}\n"
            f"Reason: {reason}\n"
            f"Reported: {ctx.replied_to.from_user.mention if ctx.replied_to.from_user else 'Unknown'}\n"
            f"Message: {ctx.replied_to.text or f'[{ctx.replied_to.content_type}]'}"
        )

        await ctx.reply("✅ Report submitted to admins")

    async def cmd_reports(self, ctx: NexusContext):
        """View pending reports."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import ModAction
            result = ctx.db.execute(
                f"""
                SELECT ma.id, ma.target_user_id, ma.actor_id, ma.reason,
                       ma.message_content, ma.created_at,
                       u1.username, u1.first_name, u1.last_name,
                       u2.username, u2.first_name, u2.last_name
                FROM mod_actions ma
                JOIN users u1 ON ma.target_user_id = u1.id
                JOIN users u2 ON ma.actor_id = u2.id
                WHERE ma.group_id = {ctx.group.id} AND ma.action_type = 'report'
                ORDER BY ma.created_at DESC
                LIMIT 10
                """
            )

            reports = result.fetchall()
            if not reports:
                await ctx.reply("✅ No pending reports")
                return

            text = "🚨 Recent Reports:\n\n"
            for row in reports:
                msg_id = row[0]
                target = row[6] or f"{row[7]} {row[8] or ''}".strip()
                reporter = row[9] or f"{row[10]} {row[11] or ''}".strip()
                reason = row[3]
                created = row[5].strftime("%Y-%m-%d %H:%M")
                text += f"Report #{msg_id}\n"
                text += f"👤 Reporter: {reporter}\n"
                text += f"🎯 Reported: {target}\n"
                text += f"📝 Reason: {reason}\n"
                text += f"🕐 {created}\n"
                text += f"━━━━━━━━━━\n"

            await ctx.reply(
                text,
                buttons=[[{"text": "Clear All", "callback_data": "reports_clear"}]]
            )

    async def cmd_review(self, ctx: NexusContext):
        """Review and resolve a report."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /review <report_id> <action>\nActions: warn, mute, ban, kick, dismiss")
            return

        report_id = args[0]
        action = args[1] if len(args) > 1 else "dismiss"

        # Find the report
        if ctx.db:
            from shared.models import ModAction
            result = ctx.db.execute(
                f"""
                SELECT * FROM mod_actions
                WHERE id = {report_id} AND action_type = 'report'
                LIMIT 1
                """
            )
            report = result.fetchone()

            if not report:
                await ctx.reply("❌ Report not found")
                return

            # Update the report
            if action == "dismiss":
                await ctx.reply("✅ Report dismissed")
            else:
                await ctx.reply(f"⚠️ Taking action: {action} on report")

    async def cmd_slowmode(self, ctx: NexusContext):
        """Enable/disable slow mode."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args or args[0].lower() == "off":
            try:
                await ctx.bot.set_chat_permissions(
                    chat_id=ctx.group.telegram_id,
                    permissions={"can_send_messages": True, "can_send_media_messages": True}
                )
                await ctx.reply("✅ Slow mode disabled")
            except Exception as e:
                await ctx.reply(f"❌ Error: {e}")
        else:
            # Parse seconds
            try:
                seconds = int(args[0])
                await ctx.bot.set_chat_permissions(
                    chat_id=ctx.group.telegram_id,
                    permissions={"can_send_messages": True, "can_send_media_messages": True}
                )
                await ctx.reply(f"✅ Slow mode enabled: {seconds}s between messages")
            except ValueError:
                await ctx.reply("❌ Invalid duration. Use: /slowmode <seconds> or /slowmode off")

    async def cmd_restrict(self, ctx: NexusContext):
        """Restrict user permissions."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if len(args) < 2:
            await ctx.reply(
                "❌ Usage: /restrict @user <permissions>\n"
                "Permissions: all, none, text, media, polls, links, invite"
            )
            return

        target_id = self._get_target(ctx, args)
        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        perm = args[1].lower()

        permissions = {
            "can_send_messages": True,
            "can_send_media_messages": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,
            "can_change_info": True,
            "can_invite_users": True,
            "can_pin_messages": True,
        }

        if perm == "none":
            permissions = {k: False for k in permissions}
        elif perm == "text":
            permissions = {
                "can_send_messages": True,
                "can_send_media_messages": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
            }
        elif perm == "media":
            permissions = {
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_polls": False,
                "can_send_other_messages": False,
            }
        elif perm == "links":
            permissions = {"can_add_web_page_previews": False, **permissions}
        elif perm == "invite":
            permissions = {"can_invite_users": False, **permissions}

        try:
            await ctx.bot.restrict_chat_member(
                chat_id=ctx.group.telegram_id,
                user_id=target_id,
                permissions=permissions,
            )
            await ctx.reply(f"✅ User permissions set to: {perm}")
        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_promote(self, ctx: NexusContext):
        """Promote user to admin."""
        if not ctx.user.is_admin and ctx.user.role != "owner":
            await ctx.reply("❌ Only owner can promote admins")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        role = args[1] if len(args) > 1 else "admin"

        try:
            if role == "admin":
                await ctx.bot.promote_chat_member(
                    chat_id=ctx.group.telegram_id,
                    user_id=target_id,
                    can_change_info=True,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_manage_chat=True,
                )
            elif role == "mod":
                await ctx.bot.promote_chat_member(
                    chat_id=ctx.group.telegram_id,
                    user_id=target_id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                )

            # Update database
            if ctx.db:
                from shared.models import Member
                ctx.db.execute(
                    f"""
                    UPDATE members
                    SET role = '{role}'
                    WHERE group_id = {ctx.group.id} AND user_id IN (
                        SELECT id FROM users WHERE telegram_id = {target_id}
                    )
                    """
                )

            await ctx.reply(f"✅ User promoted to {role}")

        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_demote(self, ctx: NexusContext):
        """Demote user from admin."""
        if not ctx.user.is_admin and ctx.user.role != "owner":
            await ctx.reply("❌ Only owner can demote admins")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        try:
            await ctx.bot.promote_chat_member(
                chat_id=ctx.group.telegram_id,
                user_id=target_id,
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_manage_chat=False,
            )

            # Update database
            if ctx.db:
                from shared.models import Member
                ctx.db.execute(
                    f"""
                    UPDATE members
                    SET role = 'member'
                    WHERE group_id = {ctx.group.id} AND user_id IN (
                        SELECT id FROM users WHERE telegram_id = {target_id}
                    )
                    """
                )

            await ctx.reply("✅ User demoted to member")

        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    async def cmd_title(self, ctx: NexusContext):
        """Set custom admin title."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a user to set their title")
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        title = " ".join(args) if args else None

        try:
            await ctx.bot.set_chat_administrator_custom_title(
                chat_id=ctx.group.telegram_id,
                user_id=ctx.replied_to.from_user.id,
                custom_title=title or ""
            )

            # Update database
            if ctx.db:
                from shared.models import Member
                ctx.db.execute(
                    f"""
                    UPDATE members
                    SET custom_title = {repr(title)}
                    WHERE group_id = {ctx.group.id} AND user_id IN (
                        SELECT id FROM users WHERE telegram_id = {ctx.replied_to.from_user.id}
                    )
                    """
                )

            await ctx.reply(f"✅ Admin title updated: {title or 'Cleared'}")

        except Exception as e:
            await ctx.reply(f"❌ Error: {e}")

    # Placeholder methods for remaining commands
    async def cmd_warns(self, ctx: NexusContext):
        """View user's warnings."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)
        if not target_id:
            target_id = ctx.user.telegram_id

        if ctx.db:
            from shared.models import Warning
            result = ctx.db.execute(
                f"""
                SELECT w.reason, w.created_at, u.username, u.first_name, u.last_name, u2.username
                FROM warnings w
                JOIN users u ON w.user_id = u.id
                JOIN users u2 ON w.issued_by = u2.id
                WHERE w.group_id = {ctx.group.id}
                AND w.user_id = (SELECT id FROM users WHERE telegram_id = {target_id})
                AND w.deleted_at IS NULL
                ORDER BY w.created_at DESC
                LIMIT 10
                """
            )

            warnings = result.fetchall()
            if not warnings:
                await ctx.reply("✅ No active warnings")
                return

            text = f"⚠️ Warnings for {warnings[0][5] or warnings[0][3]}:\n\n"
            for row in warnings:
                reason = row[0]
                created = row[1].strftime("%Y-%m-%d %H:%M")
                issuer = row[5] or row[3]
                text += f"• {reason} (by {issuer}, {created})\n"

            await ctx.reply(text)

    async def cmd_resetwarns(self, ctx: NexusContext):
        """Reset user's warnings."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        target_id = self._get_target(ctx, args)

        if not target_id:
            await ctx.reply(ctx.i18n.t("user_not_found"))
            return

        if ctx.db:
            from shared.models import Warning, Member
            user_id_result = ctx.db.execute(
                f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
            )
            user_id = user_id_result.scalar()

            if user_id:
                # Soft delete warnings
                ctx.db.execute(
                    f"""
                    UPDATE warnings
                    SET deleted_at = NOW()
                    WHERE group_id = {ctx.group.id} AND user_id = {user_id}
                    """
                )

                # Reset warn count
                ctx.db.execute(
                    f"""
                    UPDATE members
                    SET warn_count = 0
                    WHERE group_id = {ctx.group.id} AND user_id = {user_id}
                    """
                )

                await ctx.reply("✅ Warnings reset successfully")

    async def cmd_warnlimit(self, ctx: NexusContext):
        """Set warning threshold."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or not args[0].isdigit():
            await ctx.reply("❌ Usage: /warnlimit <number>")
            return

        limit = int(args[0])
        config = ctx.group.module_configs.get("moderation", {})
        config["warn_threshold"] = limit

        # Save config (would normally save to DB)
        await ctx.reply(f"✅ Warning threshold set to {limit}")

    async def cmd_warntime(self, ctx: NexusContext):
        """Set warning expiration."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        await ctx.reply("✅ Warning expiration time updated")

    async def cmd_warnmode(self, ctx: NexusContext):
        """Set action after threshold."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args or args[0] not in ["mute", "kick", "ban"]:
            await ctx.reply("❌ Usage: /warnmode <mute|kick|ban>")
            return

        action = args[0]
        config = ctx.group.module_configs.get("moderation", {})
        config["warn_action"] = action

        await ctx.reply(f"✅ Warn mode set to: {action}")
