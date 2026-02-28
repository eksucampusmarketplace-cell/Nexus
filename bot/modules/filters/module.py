"""Filters module implementation."""

import re
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class FiltersConfig(BaseModel):
    """Filters module configuration."""
    max_filters: int = 100
    max_trigger_length: int = 200


class FiltersModule(NexusModule):
    """Keyword auto-responses module."""

    name = "filters"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Auto-responses based on keywords"
    category = ModuleCategory.UTILITY

    config_schema = FiltersConfig
    default_config = FiltersConfig().dict()

    commands = [
        CommandDef(
            name="filter",
            description="Add a keyword filter.",
            admin_only=True,
            args="<trigger> <response>",
        ),
        CommandDef(
            name="filters",
            description="List all filters.",
            admin_only=True,
        ),
        CommandDef(
            name="stop",
            description="Remove a filter.",
            admin_only=True,
            args="<trigger>",
        ),
        CommandDef(
            name="stopall",
            description="Remove all filters.",
            admin_only=True,
        ),
    ]

    listeners = [EventType.MESSAGE]

    async def on_message(self, ctx: NexusContext) -> bool:
        """Handle messages."""
        if not ctx.message or not ctx.message.text:
            return False

        text = ctx.message.text
        command = text.split()[0].lower()

        if command == "/filter":
            return await self._handle_filter(ctx)
        elif command == "/filters":
            return await self._handle_list(ctx)
        elif command == "/stop":
            return await self._handle_stop(ctx)
        elif command == "/stopall":
            return await self._handle_stopall(ctx)

        # Check for filter matches
        return await self._check_filters(ctx)

    async def _handle_filter(self, ctx: NexusContext) -> bool:
        """Handle /filter command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split(maxsplit=1)
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /filter <trigger> <response>")
            return True

        parts = text[1].split(maxsplit=1)
        if len(parts) < 2:
            await ctx.reply("⚠️ Usage: /filter <trigger> <response>")
            return True

        trigger = parts[0].lower()
        response = parts[1]

        if ctx.db:
            await ctx.db.execute(
                f"""
                INSERT INTO filters (group_id, trigger, response_content, created_by)
                VALUES ({ctx.group.id}, '{trigger}', '{response.replace(chr(39), chr(39)*2)}', {ctx.user.user_id})
                ON CONFLICT (group_id, trigger) DO UPDATE
                SET response_content = EXCLUDED.response_content, created_by = EXCLUDED.created_by
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"✅ Filter added: '{trigger}' → response")
        return True

    async def _check_filters(self, ctx: NexusContext) -> bool:
        """Check if message triggers any filters."""
        if not ctx.db:
            return False

        if not ctx.message or not ctx.message.text:
            return False

        from shared.models import Filter
        result = await ctx.db.execute(
            f"""
            SELECT trigger, response_content, match_type FROM filters
            WHERE group_id = {ctx.group.id}
            """
        )
        filters = result.fetchall()

        text = ctx.message.text.lower()

        for trigger, response, match_type in filters:
            triggered = False

            if match_type == "exact":
                triggered = text == trigger.lower()
            elif match_type == "contains":
                triggered = trigger.lower() in text
            elif match_type == "startswith":
                triggered = text.startswith(trigger.lower())
            elif match_type == "endswith":
                triggered = text.endswith(trigger.lower())
            elif match_type == "regex":
                try:
                    triggered = bool(re.search(trigger, text, re.IGNORECASE))
                except re.error:
                    pass

            if triggered:
                await ctx.reply(response)
                return True

        return False

    async def _handle_list(self, ctx: NexusContext) -> bool:
        """Handle /filters command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if not ctx.db:
            return True

        from shared.models import Filter
        result = await ctx.db.execute(
            f"""
            SELECT trigger FROM filters
            WHERE group_id = {ctx.group.id}
            ORDER BY trigger
            """
        )
        filters = [row[0] for row in result.fetchall()]

        if filters:
            text = "🔍 <b>Active Filters:</b>\n\n"
            text += "\n".join(f"  • {f}" for f in filters)
        else:
            text = "🔍 No filters set.\n\nUse /filter to create one."

        await ctx.reply(text)
        return True

    async def _handle_stop(self, ctx: NexusContext) -> bool:
        """Handle /stop command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split()
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /stop <trigger>")
            return True

        trigger = text[1].lower()

        if ctx.db:
            await ctx.db.execute(
                f"""
                DELETE FROM filters
                WHERE group_id = {ctx.group.id} AND trigger = '{trigger}'
                """
            )
            await ctx.db.commit()

        await ctx.reply(f"✅ Filter '{trigger}' removed.")
        return True

    async def _handle_stopall(self, ctx: NexusContext) -> bool:
        """Handle /stopall command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if ctx.db:
            await ctx.db.execute(
                f"""
                DELETE FROM filters
                WHERE group_id = {ctx.group.id}
                """
            )
            await ctx.db.commit()

        await ctx.reply("✅ All filters removed.")
        return True
