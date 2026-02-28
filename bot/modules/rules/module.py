"""Rules module implementation."""

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, EventType, ModuleCategory, NexusModule


class RulesConfig(BaseModel):
    """Rules module configuration."""
    show_on_join: bool = True
    send_as_dm: bool = False


class RulesModule(NexusModule):
    """Group rules module."""

    name = "rules"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Group rules management"
    category = ModuleCategory.UTILITY

    config_schema = RulesConfig
    default_config = RulesConfig().dict()

    commands = [
        CommandDef(
            name="rules",
            description="Show group rules.",
        ),
        CommandDef(
            name="setrules",
            description="Set group rules.",
            admin_only=True,
            args="<text>",
        ),
        CommandDef(
            name="resetrules",
            description="Reset rules to empty.",
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

        if command == "/rules":
            return await self._handle_rules(ctx)
        elif command == "/setrules":
            return await self._handle_setrules(ctx)
        elif command == "/resetrules":
            return await self._handle_resetrules(ctx)

        return False

    async def _handle_rules(self, ctx: NexusContext) -> bool:
        """Handle /rules command."""
        if not ctx.db:
            return True

        from shared.models import Rule
        result = await ctx.db.execute(
            f"SELECT content FROM rules WHERE group_id = {ctx.group.id}"
        )
        row = result.fetchone()

        if row and row[0]:
            await ctx.reply(f"📜 <b>Group Rules:</b>\n\n{row[0]}")
        else:
            await ctx.reply("📜 No rules set for this group yet.")

        return True

    async def _handle_setrules(self, ctx: NexusContext) -> bool:
        """Handle /setrules command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        text = ctx.message.text.split(maxsplit=1)
        if len(text) < 2:
            await ctx.reply("⚠️ Usage: /setrules <text>")
            return True

        content = text[1]

        if ctx.db:
            from shared.models import Rule
            await ctx.db.execute(
                f"""
                INSERT INTO rules (group_id, content, updated_by)
                VALUES ({ctx.group.id}, '{content.replace(chr(39), chr(39)*2)}', {ctx.user.user_id})
                ON CONFLICT (group_id) DO UPDATE
                SET content = EXCLUDED.content, updated_by = EXCLUDED.updated_by, updated_at = NOW()
                """
            )
            await ctx.db.commit()

        await ctx.reply("✅ Rules updated!")
        return True

    async def _handle_resetrules(self, ctx: NexusContext) -> bool:
        """Handle /resetrules command."""
        if not ctx.user.is_admin:
            await ctx.reply("❌ Admin only.")
            return True

        if ctx.db:
            from shared.models import Rule
            await ctx.db.execute(
                f"DELETE FROM rules WHERE group_id = {ctx.group.id}"
            )
            await ctx.db.commit()

        await ctx.reply("✅ Rules cleared.")
        return True
