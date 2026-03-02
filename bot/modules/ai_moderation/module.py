"""AI Moderation Module for Nexus.

Provides AI-powered content moderation:
- Real-time message scanning
- Flagged content queue for admin review
- Auto-action for high-confidence violations
- Confidence scoring for each flag
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule
from bot.services.ai_moderation_service import AIModerationService


class AIModerationModuleConfig(BaseModel):
    """Configuration for AI moderation."""
    enabled: bool = False
    auto_action: bool = True
    notify_admins: bool = True


class AIModerationModule(NexusModule):
    """AI-powered content moderation."""

    name = "ai_moderation"
    version = "1.0.0"
    author = "Nexus Team"
    description = "AI moderation queue with confidence scoring and admin review"
    category = ModuleCategory.MODERATION

    config_schema = AIModerationModuleConfig
    default_config = AIModerationModuleConfig().dict()

    commands = [
        CommandDef(
            name="aimod",
            description="View AI moderation queue",
            admin_only=True,
        ),
        CommandDef(
            name="aimodstats",
            description="View AI moderation statistics",
            admin_only=True,
        ),
        CommandDef(
            name="review",
            description="Review a flagged item",
            admin_only=True,
            args="<item_id> <action>",
        ),
        CommandDef(
            name="aimodconfig",
            description="Configure AI moderation",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("aimod", self.cmd_ai_mod_queue)
        self.register_command("aimodstats", self.cmd_ai_mod_stats)
        self.register_command("review", self.cmd_review)
        self.register_command("aimodconfig", self.cmd_ai_mod_config)

        self.openai_key = os.getenv("OPENAI_API_KEY")

    async def on_message(self, ctx: NexusContext) -> bool:
        """Scan messages with AI moderation."""
        config = AIModerationModuleConfig(**ctx.group.module_configs.get("ai_moderation", {}))

        if not config.enabled:
            return False

        if not ctx.message:
            return False

        # Skip admin messages
        if ctx.user.is_admin:
            return False

        # Initialize AI moderation service
        service = AIModerationService(ctx.db, self.openai_key)

        # Determine content type
        content = ctx.message.text or ctx.message.caption
        media_type = None
        media_file_id = None

        if ctx.message.photo:
            media_type = "photo"
            media_file_id = ctx.message.photo[-1].file_id
        elif ctx.message.video:
            media_type = "video"
            media_file_id = ctx.message.video.file_id
        elif ctx.message.document:
            media_type = "document"
            media_file_id = ctx.message.document.file_id
        elif ctx.message.sticker:
            media_type = "sticker"
            media_file_id = ctx.message.sticker.file_id

        # Analyze message
        prediction = await service.analyze_message(
            group_id=ctx.group.id,
            user_id=ctx.user.user_id,
            message_id=ctx.message.message_id,
            content=content,
            media_type=media_type,
            media_file_id=media_file_id,
            is_forwarded=ctx.message.forward_date is not None,
        )

        if prediction and prediction.flagged:
            # Message was flagged
            if config.notify_admins and prediction.confidence >= 70:
                # Notify admins about flagged content
                await ctx.notify_admins(
                    f"🤖 **AI Moderation Alert**\n\n"
                    f"User: {ctx.user.mention}\n"
                    f"Confidence: {prediction.confidence:.0f}%\n"
                    f"Severity: {prediction.severity}\n"
                    f"Categories: {', '.join(prediction.categories)}\n\n"
                    f"Reasoning: {prediction.reasoning[:200]}...\n\n"
                    f"Use `/aimod` to review queue."
                )

            # If auto-action and high confidence, take action
            if (
                config.auto_action
                and prediction.suggested_action == "auto_executed"
            ):
                # Delete message
                await ctx.delete_message(ctx.message.message_id)

                # Notify user
                await ctx.reply(
                    f"⚠️ Your message was automatically removed.\n"
                    f"Reason: {', '.join(prediction.categories)}\n"
                    f"If you believe this was a mistake, contact an admin."
                )

                return True

        return False

    async def cmd_ai_mod_queue(self, ctx: NexusContext):
        """View AI moderation queue."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        config = AIModerationModuleConfig(**ctx.group.module_configs.get("ai_moderation", {}))

        if not config.enabled:
            await ctx.reply(
                "❌ AI moderation is not enabled.\n"
                "Enable it with: /aimodconfig enable"
            )
            return

        service = AIModerationService(ctx.db, self.openai_key)
        queue = await service.get_queue(ctx.group.id, status="pending", limit=10)

        if not queue:
            await ctx.reply("✅ No items pending review in the AI moderation queue.")
            return

        text = "🤖 **AI Moderation Queue**\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for item in queue:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(item.severity, "⚪")

            text += (
                f"#{item.id} {severity_emoji} **{item.severity.upper()}**\n"
                f"Confidence: {item.confidence:.0f}%\n"
                f"Categories: {', '.join(item.categories)}\n"
                f"Suggested: {item.suggested_action}\n"
                f"Preview: {item.message_content[:50] if item.message_content else '[Media]'}...\n"
            )

            text += f"Review: `/review {item.id} <action>`\n\n"

        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "Actions: `approve`, `dismiss`, `delete`, `mute`, `ban`, `warn`"

        await ctx.reply(text)

    async def cmd_ai_mod_stats(self, ctx: NexusContext):
        """View AI moderation statistics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        service = AIModerationService(ctx.db, self.openai_key)
        stats = await service.get_stats(ctx.group.id, days=30)

        text = (
            f"📊 **AI Moderation Statistics** (30 days)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 **Overview**\n"
            f"• Total flagged: {stats['total_flagged']}\n"
            f"• Accuracy: {stats['accuracy']:.1f}%\n"
            f"• Pending review: {stats['pending_review']}\n"
            f"• Auto actions: {stats['auto_actions']}\n\n"
            f"📈 **By Status**\n"
        )

        for status, count in stats['by_status'].items():
            text += f"• {status}: {count}\n"

        text += "\n🚨 **By Severity**\n"
        for severity, count in stats['by_severity'].items():
            text += f"• {severity}: {count}\n"

        if stats['by_category']:
            text += "\n🏷️ **By Category**\n"
            for category, count in sorted(stats['by_category'].items(), key=lambda x: -x[1])[:5]:
                text += f"• {category}: {count}\n"

        await ctx.reply(text)

    async def cmd_review(self, ctx: NexusContext):
        """Review a flagged item."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /review <item_id> <action>\nActions: approve, dismiss, delete, mute, ban, warn")
            return

        try:
            item_id = int(args[0])
        except ValueError:
            await ctx.reply("❌ Item ID must be a number")
            return

        action = args[1].lower()

        if action not in ["approve", "dismiss", "delete", "mute", "ban", "warn"]:
            await ctx.reply("❌ Invalid action. Use: approve, dismiss, delete, mute, ban, warn")
            return

        service = AIModerationService(ctx.db, self.openai_key)
        success = await service.review_item(
            item_id=item_id,
            admin_user_id=ctx.user.user_id,
            action=action,
        )

        if success:
            await ctx.reply(f"✅ Item #{item_id} reviewed: **{action}**")
        else:
            await ctx.reply(f"❌ Could not review item #{item_id}. It may have already been reviewed.")

    async def cmd_ai_mod_config(self, ctx: NexusContext):
        """Configure AI moderation."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            # Show current config
            config = AIModerationModuleConfig(**ctx.group.module_configs.get("ai_moderation", {}))

            status = "✅ Enabled" if config.enabled else "❌ Disabled"
            auto_action = "✅ On" if config.auto_action else "❌ Off"
            notify = "✅ On" if config.notify_admins else "❌ Off"

            await ctx.reply(
                f"⚙️ **AI Moderation Configuration**\n\n"
                f"Status: {status}\n"
                f"Auto-action: {auto_action}\n"
                f"Notify admins: {notify}\n\n"
                f"Commands:\n"
                f"• `/aimodconfig enable` - Enable AI moderation\n"
                f"• `/aimodconfig disable` - Disable AI moderation\n"
                f"• `/aimodconfig auto <on/off>` - Toggle auto-action\n"
                f"• `/aimodconfig notify <on/off>` - Toggle admin notifications"
            )
            return

        subcommand = args[0].lower()
        current_config = ctx.group.module_configs.get("ai_moderation", {})

        if subcommand == "enable":
            current_config["enabled"] = True
            ctx.group.module_configs["ai_moderation"] = current_config
            await ctx.reply("✅ AI moderation enabled.\n\n⚠️ Note: This requires an OpenAI API key to be configured.")

        elif subcommand == "disable":
            current_config["enabled"] = False
            ctx.group.module_configs["ai_moderation"] = current_config
            await ctx.reply("❌ AI moderation disabled.")

        elif subcommand == "auto":
            if len(args) < 2:
                await ctx.reply("❌ Usage: /aimodconfig auto <on/off>")
                return
            value = args[1].lower() == "on"
            current_config["auto_action"] = value
            ctx.group.module_configs["ai_moderation"] = current_config
            await ctx.reply(f"✅ Auto-action {'enabled' if value else 'disabled'}.")

        elif subcommand == "notify":
            if len(args) < 2:
                await ctx.reply("❌ Usage: /aimodconfig notify <on/off>")
                return
            value = args[1].lower() == "on"
            current_config["notify_admins"] = value
            ctx.group.module_configs["ai_moderation"] = current_config
            await ctx.reply(f"✅ Admin notifications {'enabled' if value else 'disabled'}.")

        else:
            await ctx.reply("❌ Unknown command. Use: enable, disable, auto, notify")
