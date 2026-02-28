"""Filters module - Keyword auto-responses."""

from typing import Optional, List, Dict
from pydantic import BaseModel
import re

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType


class FilterConfig(BaseModel):
    """Configuration for filters module."""
    filters_enabled: bool = True


class FiltersModule(NexusModule):
    """Keyword auto-responses."""

    name = "filters"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Auto-respond to keywords"
    category = ModuleCategory.UTILITY

    config_schema = FilterConfig
    default_config = FilterConfig().dict()

    commands = [
        CommandDef(
            name="filter",
            description="Create or view a filter",
            admin_only=True,
            args="<trigger>",
        ),
        CommandDef(
            name="stop",
            description="Remove a filter",
            admin_only=True,
            args="<trigger>",
        ),
        CommandDef(
            name="filters",
            description="List all filters",
            admin_only=False,
        ),
        CommandDef(
            name="stopall",
            description="Remove all filters",
            admin_only=True,
        ),
    ]

    listeners = [
        EventType.MESSAGE,
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("filter", self.cmd_filter)
        self.register_command("stop", self.cmd_stop)
        self.register_command("filters", self.cmd_filters)
        self.register_command("stopall", self.cmd_stopall)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle keyword triggers."""
        if not ctx.message or not ctx.message.text:
            return False

        config = ctx.group.module_configs.get("filters", {})
        if not config.get("filters_enabled", True):
            return False

        # Get all active filters
        if ctx.db:
            from shared.models import Filter
            result = ctx.db.execute(
                f"""
                SELECT * FROM filters
                WHERE group_id = {ctx.group.id}
                ORDER BY id ASC
                """
            )

            filters = result.fetchall()

            for filter_row in filters:
                trigger = filter_row[2]
                match_type = filter_row[3]
                response_type = filter_row[4]
                response_content = filter_row[5]
                response_file_id = filter_row[6]
                action = filter_row[7]
                delete_trigger = filter_row[8]
                admin_only = filter_row[9]
                case_sensitive = filter_row[10]

                # Check admin-only
                if admin_only and not ctx.user.is_admin:
                    continue

                # Check if trigger matches
                if self._matches_trigger(ctx.message.text, trigger, match_type, case_sensitive):
                    # Take action
                    if delete_trigger:
                        await ctx.delete_message()

                    if action == "warn":
                        await ctx.warn_user(reason=f"Triggered filter: {trigger}")
                    elif action == "mute":
                        duration = 300  # 5 minutes default
                        await ctx.mute_user(duration=duration, reason=f"Triggered filter: {trigger}")
                    elif action == "kick":
                        await ctx.kick_user(reason=f"Triggered filter: {trigger}")
                    elif action == "ban":
                        await ctx.ban_user(reason=f"Triggered filter: {trigger}")
                    elif action == "delete":
                        await ctx.delete_message()

                    # Send response
                    if response_type == "text":
                        await ctx.reply(response_content)
                    elif response_type == "photo" and response_file_id:
                        await ctx.reply_media(response_file_id, "photo", caption=response_content)
                    elif response_type == "video" and response_file_id:
                        await ctx.reply_media(response_file_id, "video", caption=response_content)
                    elif response_type == "document" and response_file_id:
                        await ctx.reply_media(response_file_id, "document", caption=response_content)
                    elif response_type == "animation" and response_file_id:
                        await ctx.reply_media(response_file_id, "animation", caption=response_content)

                    return True

        return False

    def _matches_trigger(self, text: str, trigger: str, match_type: str, case_sensitive: bool) -> bool:
        """Check if text matches trigger."""
        text_to_check = text if case_sensitive else text.lower()
        trigger_to_check = trigger if case_sensitive else trigger.lower()

        try:
            if match_type == "exact":
                return text_to_check == trigger_to_check
            elif match_type == "contains":
                return trigger_to_check in text_to_check
            elif match_type == "startswith":
                return text_to_check.startswith(trigger_to_check)
            elif match_type == "endswith":
                return text_to_check.endswith(trigger_to_check)
            elif match_type == "regex":
                pattern = re.compile(trigger)
                return bool(pattern.search(text_to_check))
            elif match_type == "fuzzy":
                # Simple fuzzy match - 80% similarity
                from difflib import SequenceMatcher
                matcher = SequenceMatcher(None, text_to_check, trigger_to_check)
                return matcher.ratio() > 0.8
        except Exception:
            return False

        return False

    async def cmd_filter(self, ctx: NexusContext):
        """Create or view a filter."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /filter <trigger> or reply with response")
            return

        trigger = args[0].lower()

        # Check if view existing
        if len(args) == 1:
            if ctx.db:
                from shared.models import Filter
                result = ctx.db.execute(
                    f"""
                    SELECT * FROM filters
                    WHERE group_id = {ctx.group.id} AND trigger = '{trigger}'
                    LIMIT 1
                    """
                )
                row = result.fetchone()

                if row:
                    text = f"📝 **Filter:** #{trigger}\n\n"
                    text += f"**Match Type:** {row[3]}\n"
                    text += f"**Response Type:** {row[4]}\n"
                    text += f"**Response:** {row[5][:100]}...\n"
                    text += f"**Action:** {row[7] or 'none'}\n"
                    text += f"**Delete Trigger:** {'Yes' if row[8] else 'No'}\n"
                    text += f"**Admin Only:** {'Yes' if row[9] else 'No'}\n"
                    await ctx.reply(text, parse_mode="Markdown")
                    return

        # Create or update filter
        response_content = None
        response_file_id = None
        response_type = "text"

        if ctx.replied_to:
            if ctx.replied_to.photo:
                response_file_id = ctx.replied_to.photo[-1].file_id
                response_type = "photo"
                response_content = ctx.replied_to.caption or ""
            elif ctx.replied_to.video:
                response_file_id = ctx.replied_to.video.file_id
                response_type = "video"
                response_content = ctx.replied_to.caption or ""
            elif ctx.replied_to.animation:
                response_file_id = ctx.replied_to.animation.file_id
                response_type = "animation"
                response_content = ctx.replied_to.caption or ""
            elif ctx.replied_to.document:
                response_file_id = ctx.replied_to.document.file_id
                response_type = "document"
                response_content = ctx.replied_to.caption or ""
            elif ctx.replied_to.text:
                response_content = ctx.replied_to.text

        if len(args) > 1:
            response_content = " ".join(args[1:])

        if not response_content and not response_file_id:
            await ctx.reply("❌ Please provide response or reply to media")
            return

        # Save to database
        if ctx.db:
            from shared.models import Filter
            existing = ctx.db.execute(
                f"""
                SELECT id FROM filters
                WHERE group_id = {ctx.group.id} AND trigger = '{trigger}'
                LIMIT 1
                """
            ).fetchone()

            if existing:
                # Update
                ctx.db.execute(
                    f"""
                    UPDATE filters
                    SET response_content = %s,
                        response_file_id = %s,
                        response_type = %s
                    WHERE id = {existing[0]}
                    """,
                    (response_content, response_file_id, response_type)
                )
                await ctx.reply(f"✅ Filter '{trigger}' updated")
            else:
                # Create
                new_filter = Filter(
                    group_id=ctx.group.id,
                    trigger=trigger,
                    match_type="contains",
                    response_type=response_type,
                    response_content=response_content,
                    response_file_id=response_file_id,
                    action=None,
                    delete_trigger=False,
                    admin_only=False,
                    case_sensitive=False,
                    created_by=ctx.user.user_id,
                )
                ctx.db.add(new_filter)
                await ctx.reply(f"✅ Filter '{trigger}' saved")

    async def cmd_stop(self, ctx: NexusContext):
        """Remove a filter."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /stop <trigger>")
            return

        trigger = args[0].lower()

        if ctx.db:
            from shared.models import Filter
            result = ctx.db.execute(
                f"""
                DELETE FROM filters
                WHERE group_id = {ctx.group.id} AND trigger = '{trigger}'
                """
            )

            await ctx.reply(f"✅ Filter '{trigger}' removed")

    async def cmd_filters(self, ctx: NexusContext):
        """List all filters."""
        if not ctx.user.is_admin and not ctx.user.is_moderator:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import Filter
            result = ctx.db.execute(
                f"""
                SELECT trigger, response_type, action, admin_only
                FROM filters
                WHERE group_id = {ctx.group.id}
                ORDER BY trigger ASC
                LIMIT 50
                """
            )

            filters = result.fetchall()

            if not filters:
                await ctx.reply("📝 No filters set yet")
                return

            text = "📝 **Active Filters:**\n\n"
            for row in filters:
                trigger = row[0]
                response_type = row[1]
                action = row[2] or "none"
                admin_only = row[3]

                action_icon = "⚠️" if action != "none" else ""
                admin_icon = "🔒" if admin_only else ""

                text += f"{admin_icon} **#{trigger}** {action_icon}\n"

            await ctx.reply(text, parse_mode="Markdown")

    async def cmd_stopall(self, ctx: NexusContext):
        """Remove all filters."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        # Confirm
        # In real implementation, show confirmation button

        if ctx.db:
            from shared.models import Filter
            ctx.db.execute(
                f"""
                DELETE FROM filters
                WHERE group_id = {ctx.group.id}
                """
            )

            await ctx.reply("✅ All filters removed")
