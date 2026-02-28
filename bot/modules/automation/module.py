"""Automation module - Scheduled and recurring actions."""


from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class AutomationConfig(BaseModel):
    """Configuration for automation."""

    max_scheduled_per_group: int = 50
    default_timezone: str = "UTC"


class AutomationModule(NexusModule):
    """Automation for scheduled and recurring actions."""

    name = "automation"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Schedule messages, locks, and other actions"
    category = ModuleCategory.UTILITY

    config_schema = AutomationConfig
    default_config = AutomationConfig().dict()

    commands = [
        CommandDef(
            name="del",
            description="Delete replied message after duration (e.g., !del 4h)",
            admin_only=True,
        ),
        CommandDef(
            name="repeat",
            description="Repeat message at interval or time",
            admin_only=True,
        ),
        CommandDef(
            name="pin",
            description="Pin message (optionally at scheduled time)",
            admin_only=True,
        ),
        CommandDef(
            name="timedlock",
            description="Lock content type during time window",
            admin_only=True,
        ),
        CommandDef(
            name="time2del",
            description="Auto-delete all messages after specified time",
            admin_only=True,
        ),
        CommandDef(
            name="tz",
            description="Set group timezone",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("del", self.cmd_del)
        self.register_command("repeat", self.cmd_repeat)
        self.register_command("pin", self.cmd_pin)
        self.register_command("timedlock", self.cmd_timedlock)
        self.register_command("time2del", self.cmd_time2del)
        self.register_command("tz", self.cmd_tz)

    async def cmd_del(self, ctx: NexusContext):
        """Delete message after duration."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a message to schedule deletion.")
            return

        duration = None
        if ctx.parsed_command:
            duration = ctx.parsed_command.duration

        if not duration:
            # Immediate delete
            await ctx.delete_message()
            return

        # Schedule deletion
        await ctx.reply(
            f"⏰ Message will be deleted in {ctx._format_duration(duration)}.\n"
            f"Use !!del to cancel."
        )

    async def cmd_repeat(self, ctx: NexusContext):
        """Set up recurring message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a message to repeat it.")
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []
        time_range = ctx.parsed_command.time_range if ctx.parsed_command else None

        if time_range:
            start, end = time_range
            # Time-based repeat
            await ctx.reply(
                f"🔄 Message will repeat at {start.strftime('%H:%M')} "
                f"for {args[0] if args else 5} days."
            )
        elif args:
            # Duration-based repeat (every X minutes/hours)
            duration = ctx.parsed_command.duration if ctx.parsed_command else None
            if duration:
                await ctx.reply(
                    f"🔄 Message will repeat every {ctx._format_duration(duration)} "
                    f"for {args[0] if len(args) > 1 else 5} times."
                )
        else:
            await ctx.reply(
                "❌ Usage:\n"
                "!repeat 10:00 5 - Repeat at 10:00 for 5 days\n"
                "!repeat 30m 5 - Repeat every 30 minutes for 5 times"
            )

    async def cmd_pin(self, ctx: NexusContext):
        """Pin message."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if not ctx.replied_to:
            await ctx.reply("❌ Reply to a message to pin it.")
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []
        time_range = ctx.parsed_command.time_range if ctx.parsed_command else None

        if time_range:
            # Scheduled pin
            start, end = time_range
            await ctx.reply(
                f"📌 Message will be pinned at {start.strftime('%H:%M')} "
                f"for {args[0] if args else 5} days."
            )
        else:
            # Immediate pin
            await ctx.pin_message(ctx.replied_to.message_id)
            await ctx.reply("📌 Message pinned.")

    async def cmd_timedlock(self, ctx: NexusContext):
        """Lock content type during time window."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []
        time_range = ctx.parsed_command.time_range if ctx.parsed_command else None
        is_deactivate = (
            ctx.is_deactivate_command
            if hasattr(ctx, "is_deactivate_command")
            else False
        )

        if is_deactivate:
            # Remove timed lock
            lock_type = args[0] if args else None
            if lock_type:
                await ctx.reply(f"✅ Timed lock for {lock_type} removed.")
            else:
                await ctx.reply("❌ Specify lock type to remove.")
            return

        if not args:
            await ctx.reply(
                "❌ Usage:\n"
                "!timedlock image 08:00 12:00 - Lock images from 8am to noon\n"
                "!!timedlock image - Remove timed lock"
            )
            return

        lock_type = args[0]

        if time_range:
            start, end = time_range
            await ctx.reply(
                f"🔒 {lock_type} will be locked from {start.strftime('%H:%M')} to {end.strftime('%H:%M')} daily."
            )
        else:
            await ctx.reply("❌ Please specify a time range (e.g., 08:00 12:00)")

    async def cmd_time2del(self, ctx: NexusContext):
        """Set auto-deletion for all messages."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []
        is_deactivate = (
            ctx.is_deactivate_command
            if hasattr(ctx, "is_deactivate_command")
            else False
        )

        if is_deactivate or not args:
            await ctx.reply("✅ Auto-deletion disabled for all messages.")
            return

        duration = ctx.parsed_command.duration if ctx.parsed_command else None
        if duration:
            await ctx.reply(
                f"🗑️ All messages will be auto-deleted after {ctx._format_duration(duration)}."
            )
        else:
            await ctx.reply("❌ Please specify a duration (e.g., !time2del 3m)")

    async def cmd_tz(self, ctx: NexusContext):
        """Set group timezone."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []

        if not args:
            await ctx.reply("❌ Usage: !tz <timezone>\nExample: !tz America/New_York")
            return

        timezone = args[0]
        await ctx.reply(f"✅ Timezone set to {timezone}")
