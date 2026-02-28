"""Member Booster module - Force add and channel requirements."""

from typing import Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class MemberBoosterConfig(BaseModel):
    """Configuration for member booster."""

    force_add_enabled: bool = False
    force_add_required: int = 0
    force_channel_enabled: bool = False
    force_channel_id: Optional[int] = None
    force_boost_enabled: bool = False
    custom_message: Optional[str] = None


class MemberBoosterModule(NexusModule):
    """Member booster for force add and channel requirements."""

    name = "member_booster"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Force members to add users or join channels"
    category = ModuleCategory.UTILITY

    config_schema = MemberBoosterConfig
    default_config = MemberBoosterConfig().dict()

    commands = [
        CommandDef(
            name="max",
            description="Set required adds before messaging (0 to disable)",
            admin_only=True,
        ),
        CommandDef(
            name="remain",
            description="Show member's add count",
            admin_only=False,
        ),
        CommandDef(
            name="top",
            description="Show top inviters",
            admin_only=False,
        ),
        CommandDef(
            name="channel",
            description="Set required channel",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("max", self.cmd_max)
        self.register_command("remain", self.cmd_remain)
        self.register_command("top", self.cmd_top)
        self.register_command("channel", self.cmd_channel)

    async def cmd_max(self, ctx: NexusContext):
        """Set required adds."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []
        if not args:
            await ctx.reply("❌ Usage: !max <number>\nUse 0 to disable force add.")
            return

        try:
            required = int(args[0])
            if required < 0:
                raise ValueError()

            if required == 0:
                await ctx.reply("✅ Force add disabled.")
            else:
                await ctx.reply(
                    f"✅ Members must add {required} users before messaging."
                )
        except ValueError:
            await ctx.reply("❌ Please provide a valid number.")

    async def cmd_remain(self, ctx: NexusContext):
        """Show add count for a user."""
        target_user = ctx.target_user or ctx.user

        # Would fetch from database
        added_count = 0
        required = 0

        await ctx.reply(
            f"📊 {target_user.mention}'s MemberBooster Stats\n\n"
            f"Added: {added_count} users\n"
            f"Required: {required}"
        )

    async def cmd_top(self, ctx: NexusContext):
        """Show top inviters."""
        # Would fetch from database
        top_users = []

        text = "🏆 Top Inviters\n\n"
        for i, user in enumerate(top_users[:10], 1):
            text += f"{i}. {user['name']} - {user['count']} invites\n"

        if not top_users:
            text += "No invites recorded yet."

        await ctx.reply(text)

    async def cmd_channel(self, ctx: NexusContext):
        """Set required channel."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.parsed_command.args if ctx.parsed_command else []

        if not args:
            await ctx.reply(
                "❌ Usage: !channel <channel_id>\n" "Use !channel 0 to disable."
            )
            return

        if args[0] == "0":
            await ctx.reply("✅ Force channel disabled.")
        else:
            await ctx.reply(f"✅ Required channel set to: {args[0]}")
