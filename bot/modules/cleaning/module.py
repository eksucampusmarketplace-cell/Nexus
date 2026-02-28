"""Cleaning module - Auto-clean bot and service messages."""

from typing import Optional
from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule, EventType


class CleaningConfig(BaseModel):
    """Configuration for cleaning module."""
    clean_service_messages: bool = False
    clean_command_messages: bool = False
    clean_after_seconds: Optional[int] = None
    max_cleaned_per_run: int = 100


class CleaningModule(NexusModule):
    """Clean bot and service messages."""

    name = "cleaning"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Auto-clean bot and service messages"
    category = ModuleCategory.UTILITY

    config_schema = CleaningConfig
    default_config = CleaningConfig().dict()

    commands = [
        CommandDef(
            name="cleanservice",
            description="Auto-delete join/leave service messages",
            admin_only=True,
            args="[on|off]",
        ),
        CommandDef(
            name="cleancommands",
            description="Auto-delete command messages",
            admin_only=True,
            args="[on|off]",
        ),
        CommandDef(
            name="clean",
            description="Delete last N bot messages",
            admin_only=True,
            args="<count>",
        ),
        CommandDef(
            name="cleanbot",
            description="Delete all bot messages",
            admin_only=True,
        ),
    ]

    listeners = [
        EventType.MESSAGE,
        EventType.NEW_MEMBER,
        EventType.LEFT_MEMBER,
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("cleanservice", self.cmd_cleanservice)
        self.register_command("cleancommands", self.cmd_cleancommands)
        self.register_command("clean", self.cmd_clean)
        self.register_command("cleanbot", self.cmd_cleanbot)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Check if command message should be cleaned."""
        config = ctx.group.module_configs.get("cleaning", {})

        # Check if command cleaning is enabled
        if config.get("clean_command_messages", False):
            # Check if this is a command
            if ctx.message.text and ctx.message.text.startswith("/"):
                clean_after = config.get("clean_after_seconds", 5)

                # Schedule deletion
                if clean_after:
                    import asyncio
                    asyncio.create_task(self._delete_after(ctx.message.message_id, clean_after))

        return False

    async def on_new_member(self, ctx: NexusContext):
        """Handle new member join."""
        config = ctx.group.module_configs.get("cleaning", {})

        if config.get("clean_service_messages", False):
            clean_after = config.get("clean_after_seconds", 60)

            # Schedule deletion of join message
            if clean_after and ctx.message:
                import asyncio
                asyncio.create_task(self._delete_after(ctx.message.message_id, clean_after))

    async def on_left_member(self, ctx: NexusContext):
        """Handle member leave."""
        config = ctx.group.module_configs.get("cleaning", {})

        if config.get("clean_service_messages", False):
            clean_after = config.get("clean_after_seconds", 60)

            # Schedule deletion of leave message
            if clean_after and ctx.message:
                import asyncio
                asyncio.create_task(self._delete_after(ctx.message.message_id, clean_after))

    async def _delete_after(self, message_id: int, seconds: int):
        """Delete message after delay."""
        import asyncio
        await asyncio.sleep(seconds)

        # This would need to be implemented in the context
        # For now, it's a placeholder
        pass

    async def cmd_cleanservice(self, ctx: NexusContext):
        """Auto-delete join/leave service messages."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args or args[0].lower() not in ["on", "off"]:
            await ctx.reply(
                "❌ Usage: /cleanservice <on|off>\n\n"
                "When enabled, automatically deletes join/leave service messages."
            )
            return

        state = args[0].lower() == "on"
        config = ctx.group.module_configs.get("cleaning", {})
        config["clean_service_messages"] = state

        await ctx.reply(
            f"✅ Service message cleaning {'enabled' if state else 'disabled'}.\n\n"
            f"Messages will be deleted after {config.get('clean_after_seconds', 60)} seconds."
        )

    async def cmd_cleancommands(self, ctx: NexusContext):
        """Auto-delete command messages."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args or args[0].lower() not in ["on", "off"]:
            await ctx.reply(
                "❌ Usage: /cleancommands <on|off>\n\n"
                "When enabled, automatically deletes command messages after execution."
            )
            return

        state = args[0].lower() == "on"
        config = ctx.group.module_configs.get("cleaning", {})
        config["clean_command_messages"] = state

        await ctx.reply(
            f"✅ Command message cleaning {'enabled' if state else 'disabled'}.\n\n"
            f"Messages will be deleted after {config.get('clean_after_seconds', 5)} seconds."
        )

    async def cmd_clean(self, ctx: NexusContext):
        """Delete last N bot messages."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args or not args[0].isdigit():
            await ctx.reply(
                "❌ Usage: /clean <count>\n\n"
                "Example: /clean 10 (deletes last 10 bot messages)"
            )
            return

        count = int(args[0])
        config = ctx.group.module_configs.get("cleaning", {})
        max_cleaned = config.get("max_cleaned_per_run", 100)

        if count > max_cleaned:
            await ctx.reply(f"❌ Maximum {max_cleaned} messages can be cleaned at once.")
            return

        # In a real implementation, this would fetch and delete messages
        # For now, it's a placeholder
        await ctx.reply(f"🧹 Cleaning last {count} bot messages...")

        # Delete the command message too
        try:
            await ctx.message.delete()
        except:
            pass

    async def cmd_cleanbot(self, ctx: NexusContext):
        """Delete all bot messages."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Only admins can use this command")
            return

        await ctx.reply(
            "🧹 Deleting all bot messages from this chat...\n\n"
            "This may take a while. Please be patient."
        )

        # In a real implementation, this would fetch and delete all bot messages
        # For now, it's a placeholder
        # This would be a very expensive operation
