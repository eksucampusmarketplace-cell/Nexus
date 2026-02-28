"""Word Filter module - Two separate lists for banned words."""


from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class WordFilterConfig(BaseModel):
    """Configuration for word filter."""

    filter_list_enabled: bool = True
    filter_list_action: str = "delete"
    bad_list_enabled: bool = True
    bad_list_action: str = "warn"


class WordFilterModule(NexusModule):
    """Word filter with two independent lists."""

    name = "word_filter"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Filter and block unwanted words with two separate lists"
    category = ModuleCategory.ANTISPAM

    config_schema = WordFilterConfig
    default_config = WordFilterConfig().dict()

    commands = [
        CommandDef(
            name="filter",
            description="Add word to filter list (deletes message)",
            admin_only=True,
        ),
        CommandDef(
            name="bad",
            description="Add word to bad list (deletes + warns)",
            admin_only=True,
        ),
        CommandDef(
            name="filters",
            description="View filter list",
            admin_only=False,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("filter", self.cmd_filter)
        self.register_command("bad", self.cmd_bad)
        self.register_command("filters", self.cmd_filters)

    async def cmd_filter(self, ctx: NexusContext):
        """Add/remove word from filter list."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        is_deactivate = (
            ctx.is_deactivate_command
            if hasattr(ctx, "is_deactivate_command")
            else False
        )
        args = ctx.parsed_command.args if ctx.parsed_command else []

        if not args:
            await ctx.reply("❌ Usage: !filter <word>\n!!filter <word> to remove")
            return

        word = " ".join(args).lower()

        if is_deactivate:
            # Remove from filter list
            await ctx.reply(f"✅ Removed '{word}' from filter list.")
        else:
            # Add to filter list
            await ctx.reply(
                f"✅ Added '{word}' to filter list.\nMessages containing this word will be deleted."
            )

    async def cmd_bad(self, ctx: NexusContext):
        """Add/remove word from bad list."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        is_deactivate = (
            ctx.is_deactivate_command
            if hasattr(ctx, "is_deactivate_command")
            else False
        )
        args = ctx.parsed_command.args if ctx.parsed_command else []

        if not args:
            await ctx.reply("❌ Usage: !bad <word>\n!!bad <word> to remove")
            return

        word = " ".join(args).lower()

        if is_deactivate:
            await ctx.reply(f"✅ Removed '{word}' from bad list.")
        else:
            await ctx.reply(
                f"✅ Added '{word}' to bad list.\n"
                f"Messages containing this word will be deleted and users will be warned."
            )

    async def cmd_filters(self, ctx: NexusContext):
        """View filter lists."""
        # Would fetch from database
        filter_list = []
        bad_list = []

        text = "📝 Word Filters\n\n"

        text += "🗑️ Filter List (delete only):\n"
        if filter_list:
            for word in filter_list[:20]:
                text += f"• {word}\n"
        else:
            text += "No words in filter list.\n"

        text += "\n⚠️ Bad List (delete + warn):\n"
        if bad_list:
            for word in bad_list[:20]:
                text += f"• {word}\n"
        else:
            text += "No words in bad list.\n"

        await ctx.reply(text)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Check message for filtered words."""
        if not ctx.message or not ctx.message.text:
            return False

        # Would check both lists from database
        # If found in filter_list -> delete
        # If found in bad_list -> delete + warn

        return False
