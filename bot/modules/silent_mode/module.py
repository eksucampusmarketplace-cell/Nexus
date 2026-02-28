"""Silent Mode module - Manage group silence periods."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class SilentModeConfig(BaseModel):
    """Configuration for silent mode."""

    is_enabled: bool = False
    until: Optional[datetime] = None
    scheduled_windows: list = []


class SilentModeModule(NexusModule):
    """Silent mode management for groups."""

    name = "silent_mode"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Enable/disable group silence with scheduling"
    category = ModuleCategory.UTILITY

    config_schema = SilentModeConfig
    default_config = SilentModeConfig().dict()

    commands = [
        CommandDef(
            name="off",
            description="Enable silent mode (no messages allowed)",
            admin_only=True,
        ),
        CommandDef(
            name="on",
            description="Disable silent mode",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("off", self.cmd_off)
        self.register_command("on", self.cmd_on)

    async def cmd_off(self, ctx: NexusContext):
        """Enable silent mode."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        # Check for duration
        duration = None
        time_range = None

        if ctx.parsed_command:
            duration = ctx.parsed_command.duration
            time_range = ctx.parsed_command.time_range

        if time_range:
            # Scheduled silent mode
            start, end = time_range
            await ctx.reply(
                f"🔇 Silent mode scheduled from {start.strftime('%H:%M')} to {end.strftime('%H:%M')}"
            )
        elif duration:
            # Timed silent mode
            await ctx.reply(
                f"🔇 Silent mode enabled for {ctx._format_duration(duration)}\n"
                f"Use !on to disable early."
            )
        else:
            # Immediate silent mode
            await ctx.reply(
                "🔇 Silent mode enabled. No messages allowed.\n" "Use !on to disable."
            )

    async def cmd_on(self, ctx: NexusContext):
        """Disable silent mode."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        await ctx.reply("🔊 Silent mode disabled. Messages are now allowed.")
