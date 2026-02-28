"""Rules module - Group rules management."""

from typing import Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class RulesConfig(BaseModel):
    """Configuration for rules module."""
    rules_enabled: bool = True
    show_on_join: bool = False
    send_as_dm: bool = False
    require_acknowledge: bool = False


class RulesModule(NexusModule):
    """Group rules system."""

    name = "rules"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Manage and display group rules"
    category = ModuleCategory.UTILITY

    config_schema = RulesConfig
    default_config = RulesConfig().dict()

    commands = [
        CommandDef(
            name="setrules",
            description="Set group rules",
            admin_only=True,
            args="<content>",
        ),
        CommandDef(
            name="rules",
            description="View group rules",
            admin_only=False,
        ),
        CommandDef(
            name="resetrules",
            description="Reset group rules to default",
            admin_only=True,
        ),
        CommandDef(
            name="clearrules",
            description="Clear all group rules",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("setrules", self.cmd_setrules)
        self.register_command("rules", self.cmd_rules)
        self.register_command("resetrules", self.cmd_resetrules)
        self.register_command("clearrules", self.cmd_clearrules)

    async def cmd_setrules(self, ctx: NexusContext):
        """Set group rules."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split(maxsplit=1)[1:] if ctx.message.text else []
        if not args:
            await ctx.reply("❌ Usage: /setrules <rules>")
            return

        content = " ".join(args)

        if ctx.db:
            from shared.models import Rule
            rule = ctx.db.execute(
                f"""
                SELECT * FROM rules WHERE group_id = {ctx.group.id}
                LIMIT 1
                """
            ).fetchone()

            if rule:
                ctx.db.execute(
                    f"""
                    UPDATE rules
                    SET content = %s,
                        updated_by = {ctx.user.user_id}
                    WHERE id = {rule[0]}
                    """,
                    (content,)
                )
            else:
                rule = Rule(
                    group_id=ctx.group.id,
                    content=content,
                    updated_by=ctx.user.user_id,
                )
                ctx.db.add(rule)

        config = ctx.group.module_configs.get("rules", {})
        config["rules_enabled"] = True

        await ctx.reply("✅ Rules updated")

    async def cmd_rules(self, ctx: NexusContext):
        """View group rules."""
        if ctx.db:
            from shared.models import Rule
            result = ctx.db.execute(
                f"SELECT content FROM rules WHERE group_id = {ctx.group.id}"
            )
            row = result.fetchone()

            if row:
                rules = row[0]
                await ctx.reply(f"📜 **Rules**\n\n{rules}")
            else:
                await ctx.reply("❌ No rules set yet. Use /setrules to set them.")

    async def cmd_resetrules(self, ctx: NexusContext):
        """Reset rules to default."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import Rule
            ctx.db.execute(
                f"""
                DELETE FROM rules WHERE group_id = {ctx.group.id}
                """
            )

        await ctx.reply("✅ Rules reset to default")

    async def cmd_clearrules(self, ctx: NexusContext):
        """Clear all rules."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import Rule
            ctx.db.execute(
                f"""
                DELETE FROM rules WHERE group_id = {ctx.group.id}
                """
            )

        config = ctx.group.module_configs.get("rules", {})
        config["rules_enabled"] = False

        await ctx.reply("✅ Rules cleared")
