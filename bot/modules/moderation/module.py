"""Moderation module implementation."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from bot.core.context import ActionType, NexusContext, Role
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class ModerationConfig(BaseModel):
    """Moderation module configuration."""
    warn_threshold: int = Field(default=3, ge=1, le=10)
    warn_action: str = "mute"  # mute, kick, ban
    warn_duration: int = Field(default=3600, ge=60)  # seconds
    warn_reset_days: int = Field(default=7, ge=1)
    mute_default_duration: int = Field(default=3600, ge=60)
    ban_default_duration: Optional[int] = None  # None = permanent
    log_channel_id: Optional[int] = None
    confirm_destructive: bool = True
    auto_delete_commands: bool = False


class ModerationModule(NexusModule):
    """Core moderation module."""

    name = "moderation"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Core moderation tools including warn, mute, ban, kick, and user management"
    category = ModuleCategory.MODERATION

    config_schema = ModerationConfig
    default_config = ModerationConfig().dict()

    commands = [
        CommandDef(
            name="warn",
            description="Warn a user. Reply to message or mention user.",
            admin_only=True,
            aliases=["w"],
            args="[reason]",
        ),
        CommandDef(
            name="warns",
            description="Show warnings for a user.",
            admin_only=True,
            args="[@user]",
        ),
        CommandDef(
            name="resetwarns",
            description="Clear all warnings for a user.",
            admin_only=True,
            aliases=["clearwarns"],
        ),
        CommandDef(
            name="mute",
            description="Mute a user. Duration: 1m, 1h, 1d, 1w",
            admin_only=True,
            aliases=["m"],
            args="[duration] [reason]",
        ),
        CommandDef(
            name="unmute",
            description="Unmute a user.",
            admin_only=True,
            aliases=["um"],
        ),
        CommandDef(
            name="ban",
            description="Ban a user. Duration optional: 1d, 1w, etc",
            admin_only=True,
            aliases=["b"],
            args="[duration] [reason]",
        ),
        CommandDef(
            name="unban",
            description="Unban a user.",
            admin_only=True,
            aliases=["ub"],
        ),
        CommandDef(
            name="tban",
            description="Temporarily ban a user with duration.",
            admin_only=True,
            args="<duration> [reason]",
        ),
        CommandDef(
            name="tmute",
            description="Temporarily mute a user with duration.",
            admin_only=True,
            args="<duration> [reason]",
        ),
        CommandDef(
            name="kick",
            description="Kick a user from the group.",
            admin_only=True,
            aliases=["k"],
            args="[reason]",
        ),
        CommandDef(
            name="kickme",
            description="Kick yourself from the group.",
            admin_only=False,
        ),
        CommandDef(
            name="promote",
            description="Promote a user to admin.",
            admin_only=True,
            aliases=["admin"],
        ),
        CommandDef(
            name="demote",
            description="Demote a user from admin.",
            admin_only=True,
        ),
        CommandDef(
            name="title",
            description="Set a custom title for a user.",
            admin_only=True,
            args="<title>",
        ),
        CommandDef(
            name="pin",
            description="Pin a message. Reply to message.",
            admin_only=True,
            aliases=["pinned"],
        ),
        CommandDef(
            name="unpin",
            description="Unpin the current pinned message.",
            admin_only=True,
        ),
        CommandDef(
            name="unpinall",
            description="Unpin all messages.",
            admin_only=True,
        ),
        CommandDef(
            name="purge",
            description="Delete multiple messages. Reply to start message.",
            admin_only=True,
            aliases=["delall"],
            args="<count>",
        ),
        CommandDef(
            name="del",
            description="Delete the replied message.",
            admin_only=True,
            aliases=["delete"],
        ),
        CommandDef(
            name="history",
            description="Show moderation history for a user.",
            admin_only=True,
            aliases=["userinfo", "ui"],
        ),
        CommandDef(
            name="trust",
            description="Trust a user (whitelist from auto-moderation).",
            admin_only=True,
        ),
        CommandDef(
            name="untrust",
            description="Remove trust from a user.",
            admin_only=True,
        ),
        CommandDef(
            name="approve",
            description="Approve a user (bypass restrictions).",
            admin_only=True,
        ),
        CommandDef(
            name="unapprove",
            description="Remove approval from a user.",
            admin_only=True,
        ),
        CommandDef(
            name="report",
            description="Report a message to admins.",
            admin_only=False,
        ),
        CommandDef(
            name="reports",
            description="View recent reports.",
            admin_only=True,
        ),
    ]

    listeners = [EventType.MESSAGE]

    async def on_command_warn(self, ctx: NexusContext) -> None:
        """Handle /warn command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        # Get target from reply or mention
        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user to warn.")
            return

        # Get reason
        reason = self._get_reason(ctx)
        silent = self._is_silent(ctx)

        # Perform warning
        ctx.set_target(target)
        ctx.set_silent(silent)
        result = await ctx.warn_user(target, reason)

        if result.threshold_reached and result.auto_action:
            await ctx.reply(
                f"⚠️ User has reached warning threshold. Auto-action applied: {result.auto_action}"
            )

    async def on_command_warns(self, ctx: NexusContext) -> None:
        """Handle /warns command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx) or ctx.user
        history = await ctx.get_user_history(target.user_id)

        text = f"📋 <b>Warnings for {target.mention}</b>\n\n"
        text += f"⚠️ Total Warnings: {history.warnings}\n"
        text += f"🔇 Times Muted: {history.mutes}\n"
        text += f"🚫 Times Banned: {history.bans}\n"
        text += f"👢 Times Kicked: {history.kicks}\n"

        await ctx.reply(text)

    async def on_command_resetwarns(self, ctx: NexusContext) -> None:
        """Handle /resetwarns command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        # Clear warnings from database
        from shared.models import Member, Warning
        if ctx.db:
            await ctx.db.execute(
                f"""
                UPDATE warnings
                SET deleted_at = NOW()
                WHERE group_id = {ctx.group.id} AND user_id = {target.user_id}
                """
            )
            await ctx.db.execute(
                f"""
                UPDATE members
                SET warn_count = 0
                WHERE id = {target.id}
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"✅ Warnings cleared for {target.mention}")

    async def on_command_mute(self, ctx: NexusContext) -> None:
        """Handle /mute command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user to mute.")
            return

        duration, reason = self._parse_duration_and_reason(ctx)
        silent = self._is_silent(ctx)

        ctx.set_target(target)
        ctx.set_silent(silent)
        await ctx.mute_user(target, duration, reason)

    async def on_command_unmute(self, ctx: NexusContext) -> None:
        """Handle /unmute command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        await ctx.unmute_user(target)
        await ctx.reply(f"✅ {target.mention} has been unmuted.")

    async def on_command_ban(self, ctx: NexusContext) -> None:
        """Handle /ban command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user to ban.")
            return

        duration, reason = self._parse_duration_and_reason(ctx)
        silent = self._is_silent(ctx)

        ctx.set_target(target)
        ctx.set_silent(silent)
        await ctx.ban_user(target, duration, reason)

    async def on_command_unban(self, ctx: NexusContext) -> None:
        """Handle /unban command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        await ctx.unban_user(target)
        await ctx.reply(f"✅ {target.mention} has been unbanned.")

    async def on_command_tban(self, ctx: NexusContext) -> None:
        """Handle /tban command."""
        await self.on_command_ban(ctx)

    async def on_command_tmute(self, ctx: NexusContext) -> None:
        """Handle /tmute command."""
        await self.on_command_mute(ctx)

    async def on_command_kick(self, ctx: NexusContext) -> None:
        """Handle /kick command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user to kick.")
            return

        reason = self._get_reason(ctx)
        ctx.set_target(target)
        await ctx.kick_user(target, reason)

    async def on_command_kickme(self, ctx: NexusContext) -> None:
        """Handle /kickme command."""
        await ctx.reply(
            "🚪 You want to leave? Click the button below:",
            buttons=[[
                {"text": "👋 Leave Group", "callback_data": "kickme_confirm"}
            ]]
        )

    async def on_command_pin(self, ctx: NexusContext) -> None:
        """Handle /pin command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("⚠️ Reply to the message you want to pin.")
            return

        notify = not self._is_silent(ctx)
        await ctx.pin_message(ctx.replied_to.message_id, notify=notify)

    async def on_command_unpin(self, ctx: NexusContext) -> None:
        """Handle /unpin command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        try:
            await ctx.bot.unpin_chat_message(ctx.group.telegram_id)
            await ctx.reply("✅ Pinned message has been unpinned.")
        except Exception as e:
            await ctx.reply(f"❌ Failed to unpin: {e}")

    async def on_command_unpinall(self, ctx: NexusContext) -> None:
        """Handle /unpinall command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        try:
            await ctx.bot.unpin_all_chat_messages(ctx.group.telegram_id)
            await ctx.reply("✅ All pinned messages have been unpinned.")
        except Exception as e:
            await ctx.reply(f"❌ Failed to unpin all: {e}")

    async def on_command_purge(self, ctx: NexusContext) -> None:
        """Handle /purge command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("⚠️ Reply to the message where you want to start purging.")
            return

        # Parse count from command
        text = ctx.message.text or ""
        parts = text.split()
        count = 10
        if len(parts) > 1:
            try:
                count = int(parts[1])
            except ValueError:
                pass

        start_id = ctx.replied_to.message_id
        end_id = min(start_id + count, ctx.message.message_id - 1)

        deleted = await ctx.purge_messages(start_id, end_id)
        await ctx.reply(f"✅ Deleted {deleted} messages.", delete_after=5)

    async def on_command_del(self, ctx: NexusContext) -> None:
        """Handle /del command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("⚠️ Reply to the message you want to delete.")
            return

        await ctx.delete_message(ctx.replied_to.message_id)
        await ctx.delete_message()

    async def on_command_history(self, ctx: NexusContext) -> None:
        """Handle /history command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            target = ctx.user

        history = await ctx.get_user_history(target.user_id)

        text = f"📊 <b>History for {target.mention}</b>\n\n"
        text += f"👤 <b>General Stats</b>\n"
        text += f"  Messages: {history.total_messages}\n"
        text += f"  Trust Score: {target.trust_score}/100\n\n"
        text += f"⚠️ <b>Moderation History</b>\n"
        text += f"  Warnings: {history.warnings}\n"
        text += f"  Mutes: {history.mutes}\n"
        text += f"  Bans: {history.bans}\n"
        text += f"  Kicks: {history.kicks}\n"

        if history.last_warning:
            text += f"\nLast Warning: {history.last_warning.strftime('%Y-%m-%d')}"

        await ctx.reply(text)

    async def on_command_trust(self, ctx: NexusContext) -> None:
        """Handle /trust command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        # Update trust status
        if ctx.db:
            from shared.models import Member
            await ctx.db.execute(
                f"""
                UPDATE members
                SET role = '{Role.TRUSTED.value}', is_whitelisted = TRUE
                WHERE id = {target.id}
                """
            )
            await ctx.db.commit()

        await ctx.update_trust_score(target.user_id, 20, "Manually trusted by admin")
        await ctx.reply(f"✅ {target.mention} has been trusted.")

    async def on_command_untrust(self, ctx: NexusContext) -> None:
        """Handle /untrust command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        if ctx.db:
            from shared.models import Member
            await ctx.db.execute(
                f"""
                UPDATE members
                SET role = '{Role.MEMBER.value}', is_whitelisted = FALSE
                WHERE id = {target.id}
                """
            )
            await ctx.db.commit()

        await ctx.update_trust_score(target.user_id, -20, "Trust removed by admin")
        await ctx.reply(f"✅ Trust removed from {target.mention}.")

    async def on_command_approve(self, ctx: NexusContext) -> None:
        """Handle /approve command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        if ctx.db:
            from shared.models import Approval, Member
            await ctx.db.execute(
                f"""
                UPDATE members
                SET is_approved = TRUE
                WHERE id = {target.id}
                """
            )

            approval = Approval(
                group_id=ctx.group.id,
                user_id=target.user_id,
                approved_by=ctx.user.user_id,
            )
            ctx.db.add(approval)
            await ctx.db.commit()

        await ctx.reply(f"✅ {target.mention} has been approved.")

    async def on_command_unapprove(self, ctx: NexusContext) -> None:
        """Handle /unapprove command."""
        if not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        target = await self._get_target(ctx)
        if not target:
            await ctx.reply("⚠️ Reply to a message or mention a user.")
            return

        if ctx.db:
            from shared.models import Member
            await ctx.db.execute(
                f"""
                UPDATE members
                SET is_approved = FALSE
                WHERE id = {target.id}
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"✅ Approval removed from {target.mention}.")

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle incoming messages."""
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text

        # Check for silent flag (! suffix)
        command_parts = text.split()
        if not command_parts:
            return False

        command = command_parts[0].lower()
        silent = command.endswith("!")
        if silent:
            command = command[:-1]

        # Map commands to handlers
        handlers = {
            "/warn": self.on_command_warn,
            "/w": self.on_command_warn,
            "/warns": self.on_command_warns,
            "/resetwarns": self.on_command_resetwarns,
            "/clearwarns": self.on_command_resetwarns,
            "/mute": self.on_command_mute,
            "/m": self.on_command_mute,
            "/unmute": self.on_command_unmute,
            "/um": self.on_command_unmute,
            "/ban": self.on_command_ban,
            "/b": self.on_command_ban,
            "/unban": self.on_command_unban,
            "/ub": self.on_command_unban,
            "/tban": self.on_command_tban,
            "/tmute": self.on_command_tmute,
            "/kick": self.on_command_kick,
            "/k": self.on_command_kick,
            "/kickme": self.on_command_kickme,
            "/pin": self.on_command_pin,
            "/unpin": self.on_command_unpin,
            "/unpinall": self.on_command_unpinall,
            "/purge": self.on_command_purge,
            "/delall": self.on_command_purge,
            "/del": self.on_command_del,
            "/delete": self.on_command_del,
            "/history": self.on_command_history,
            "/userinfo": self.on_command_history,
            "/ui": self.on_command_history,
            "/trust": self.on_command_trust,
            "/untrust": self.on_command_untrust,
            "/approve": self.on_command_approve,
            "/unapprove": self.on_command_unapprove,
        }

        handler = handlers.get(command)
        if handler:
            await handler(ctx)
            return True

        return False

    async def _get_target(self, ctx: NexusContext) -> Optional[Any]:
        """Get target user from reply or mention."""
        if ctx.replied_to and ctx.replied_to.from_user:
            # Get member from database
            from shared.models import Member, User
            if ctx.db:
                result = await ctx.db.execute(
                    f"""
                    SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                    FROM members m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.group_id = {ctx.group.id}
                    AND u.telegram_id = {ctx.replied_to.from_user.id}
                    """
                )
                row = result.fetchone()
                if row:
                    return ctx.user.__class__(
                        id=row[0],
                        user_id=row[1],
                        group_id=row[2],
                        telegram_id=row[15],
                        username=row[16],
                        first_name=row[17],
                        last_name=row[18],
                        role=Role(row[11]),
                        trust_score=row[8],
                        xp=row[9],
                        level=row[10],
                        warn_count=row[13],
                        is_muted=row[17],
                        is_banned=row[19],
                        is_approved=row[21],
                        is_whitelisted=row[22],
                        joined_at=row[3],
                        message_count=row[5],
                        custom_title=row[23],
                    )

        # Try to get from mentions
        if ctx.message.entities:
            for entity in ctx.message.entities:
                if entity.type == "mention":
                    username = ctx.message.text[entity.offset:entity.offset + entity.length]
                    if ctx.db:
                        from shared.models import Member, User
                        result = await ctx.db.execute(
                            f"""
                            SELECT m.*, u.telegram_id, u.username, u.first_name, u.last_name
                            FROM members m
                            JOIN users u ON m.user_id = u.id
                            WHERE m.group_id = {ctx.group.id}
                            AND u.username = '{username[1:]}'
                            """
                        )
                        row = result.fetchone()
                        if row:
                            return ctx.user.__class__(
                                id=row[0],
                                user_id=row[1],
                                group_id=row[2],
                                telegram_id=row[15],
                                username=row[16],
                                first_name=row[17],
                                last_name=row[18],
                                role=Role(row[11]),
                                trust_score=row[8],
                                xp=row[9],
                                level=row[10],
                                warn_count=row[13],
                                is_muted=row[17],
                                is_banned=row[19],
                                is_approved=row[21],
                                is_whitelisted=row[22],
                                joined_at=row[3],
                                message_count=row[5],
                                custom_title=row[23],
                            )

        return None

    def _get_reason(self, ctx: NexusContext) -> Optional[str]:
        """Extract reason from command."""
        text = ctx.message.text or ""
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            return parts[1].strip()
        return None

    def _parse_duration_and_reason(self, ctx: NexusContext) -> tuple[Optional[int], Optional[str]]:
        """Parse duration and reason from command."""
        text = ctx.message.text or ""
        parts = text.split(maxsplit=2)

        if len(parts) < 2:
            return None, None

        duration = ctx.parse_duration(parts[1])
        if duration:
            reason = parts[2] if len(parts) > 2 else None
            return duration, reason
        else:
            # No duration, treat rest as reason
            reason = parts[1] if len(parts) > 1 else None
            return None, reason

    def _is_silent(self, ctx: NexusContext) -> bool:
        """Check if command has silent flag."""
        text = ctx.message.text or ""
        return text.split()[0].endswith("!")
