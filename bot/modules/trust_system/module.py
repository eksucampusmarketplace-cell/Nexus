"""Trust Score System Module for Nexus.

Integrates behavioral reputation scoring with moderation:
- Trusted users get leniency in moderation
- Trust score influences auto-approval
- Track trust history and trends
- Cross-module intelligence integration
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule
from bot.services.trust_engine import TrustEngine


class TrustSystemConfig(BaseModel):
    """Configuration for trust system."""
    enabled: bool = True
    influence_moderation: bool = True
    public_leaderboard: bool = False
    announce_threshold_reached: bool = True


class TrustSystemModule(NexusModule):
    """Behavioral trust score system."""

    name = "trust_system"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Behavioral reputation scoring that influences moderation decisions"
    category = ModuleCategory.MODERATION

    config_schema = TrustSystemConfig
    default_config = TrustSystemConfig().dict()

    commands = [
        CommandDef(
            name="trustscore",
            description="View your trust score",
            admin_only=False,
            aliases=["trust", "mytrust"],
        ),
        CommandDef(
            name="trustreport",
            description="View detailed trust report",
            admin_only=False,
        ),
        CommandDef(
            name="trustleaderboard",
            description="View trust score leaderboard",
            admin_only=False,
            aliases=["trusttop"],
        ),
        CommandDef(
            name="admintrust",
            description="View trust report for user (admin)",
            admin_only=True,
            args="@user",
        ),
        CommandDef(
            name="adjusttrust",
            description="Manually adjust trust score (admin)",
            admin_only=True,
            args="@user <delta> <reason>",
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("trustscore", self.cmd_trust_score)
        self.register_command("trust", self.cmd_trust_score)
        self.register_command("mytrust", self.cmd_trust_score)
        self.register_command("trustreport", self.cmd_trust_report)
        self.register_command("trustleaderboard", self.cmd_trust_leaderboard)
        self.register_command("trusttop", self.cmd_trust_leaderboard)
        self.register_command("admintrust", self.cmd_admin_trust)
        self.register_command("adjusttrust", self.cmd_adjust_trust)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Process trust-affecting events."""
        config = TrustSystemConfig(**ctx.group.module_configs.get("trust_system", {}))

        if not config.enabled:
            return False

        if not ctx.message:
            return False

        # Initialize trust engine
        engine = TrustEngine(ctx.db)

        # Award trust for message (small amount)
        await engine.process_event(
            ctx.group.id,
            ctx.user.user_id,
            "message_sent",
        )

        # Check for quality contribution
        if ctx.message.text and len(ctx.message.text) > 100:
            # Longer messages might be quality contributions
            await engine.process_event(
                ctx.group.id,
                ctx.user.user_id,
                "quality_contribution",
            )

        return False

    async def cmd_trust_score(self, ctx: NexusContext):
        """View your trust score."""
        config = TrustSystemConfig(**ctx.group.module_configs.get("trust_system", {}))

        if not config.enabled:
            await ctx.reply("❌ Trust system is not enabled in this group.")
            return

        engine = TrustEngine(ctx.db)

        # Get or calculate trust score
        score = await engine.calculate_trust_score(ctx.group.id, ctx.user.user_id)

        # Determine tier
        tier = engine._get_tier(score)

        # Tier emoji
        tier_emojis = {
            "trusted": "🌟",
            "neutral": "⭐",
            "suspicious": "⚠️",
            "untrusted": "❌",
        }

        # Build progress bar
        filled = int(score / 5)
        bar = "█" * filled + "░" * (20 - filled)

        text = (
            f"{tier_emojis.get(tier, '⭐')} **Your Trust Score**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Score: **{score}/100**\n"
            f"[{bar}]\n\n"
            f"Tier: **{tier.title()}**\n"
        )

        if tier == "trusted":
            text += "✅ You have moderation bypass privileges\n"
        elif tier == "suspicious":
            text += "⚠️ Build trust through positive contributions\n"

        text += "\n📊 Use /trustreport for detailed analysis"

        await ctx.reply(text)

    async def cmd_trust_report(self, ctx: NexusContext):
        """View detailed trust report."""
        config = TrustSystemConfig(**ctx.group.module_configs.get("trust_system", {}))

        if not config.enabled:
            await ctx.reply("❌ Trust system is not enabled.")
            return

        engine = TrustEngine(ctx.db)
        report = await engine.get_trust_report(ctx.group.id, ctx.user.user_id)

        # Change indicators
        change_7d_emoji = "📈" if report.score_change_7d > 0 else "📉" if report.score_change_7d < 0 else "➡️"
        change_30d_emoji = "📈" if report.score_change_30d > 0 else "📉" if report.score_change_30d < 0 else "➡️"

        text = (
            f"📊 **Trust Report**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Current Score: **{report.current_score}/100**\n"
            f"Tier: **{report.tier.title()}**\n\n"
            f"📈 **Changes**\n"
            f"• 7 days: {change_7d_emoji} {report.score_change_7d:+,}\n"
            f"• 30 days: {change_30d_emoji} {report.score_change_30d:+,}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        # Contributing factors
        if report.contributing_factors:
            text += "🎯 **Contributing Factors**\n"
            for factor, score in report.contributing_factors.items():
                bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                text += f"• {factor.title()}: [{bar}] {score:.0f}\n"
            text += "\n"

        # Recommendations
        if report.recommended_actions:
            text += "💡 **Recommendations**\n"
            for rec in report.recommended_actions[:3]:
                text += f"• {rec.replace('_', ' ').title()}\n"

        await ctx.reply(text)

    async def cmd_trust_leaderboard(self, ctx: NexusContext):
        """View trust score leaderboard."""
        config = TrustSystemConfig(**ctx.group.module_configs.get("trust_system", {}))

        if not config.enabled:
            await ctx.reply("❌ Trust system is not enabled.")
            return

        if not config.public_leaderboard and not ctx.user.is_admin:
            await ctx.reply("❌ Trust leaderboard is private. Ask an admin to enable it.")
            return

        engine = TrustEngine(ctx.db)
        leaderboard = await engine.get_leaderboard(ctx.group.id, limit=10)

        if not leaderboard:
            await ctx.reply("📊 No trust data yet.")
            return

        text = "🏆 **Trust Score Leaderboard**\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for entry in leaderboard:
            rank = entry["rank"]
            score = entry["trust_score"]
            tier = entry["tier"]

            # Rank emoji
            rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")

            # Tier emoji
            tier_emoji = {
                "trusted": "🌟",
                "neutral": "⭐",
                "suspicious": "⚠️",
            }.get(tier, "⭐")

            text += f"{rank_emoji} User {entry['user_id']}: {score} {tier_emoji}\n"

        await ctx.reply(text)

    async def cmd_admin_trust(self, ctx: NexusContext):
        """View trust report for user (admin)."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        # Get target user from args or reply
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        target_id = None
        if ctx.replied_to and ctx.replied_to.from_user:
            target_id = ctx.replied_to.from_user.id
        elif args:
            # Try to parse username
            username = args[0].lstrip("@")
            # Would need to resolve username to ID
            await ctx.reply("❌ Please reply to a user's message to check their trust.")
            return

        if not target_id:
            await ctx.reply("❌ Please reply to a user's message.")
            return

        engine = TrustEngine(ctx.db)

        # Get user from database
        from shared.models import User, Member

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
        )
        row = result.fetchone()

        if not row:
            await ctx.reply("❌ User not found.")
            return

        user_db_id = row[0]
        report = await engine.get_trust_report(ctx.group.id, user_db_id)

        text = (
            f"👮 **Admin Trust Report**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"User ID: {target_id}\n"
            f"Current Score: **{report.current_score}/100**\n"
            f"Tier: **{report.tier.title()}**\n\n"
            f"7-day change: {report.score_change_7d:+,}\n"
            f"30-day change: {report.score_change_30d:+,}\n\n"
        )

        # Moderation context
        mod_context = await engine.get_moderation_context(
            ctx.group.id, user_db_id, "warn"
        )

        text += f"Moderation leniency: {'Yes' if mod_context.apply_leniency else 'No'}\n"
        if mod_context.reasoning:
            text += f"Reason: {', '.join(mod_context.reasoning)}\n"

        await ctx.reply(text)

    async def cmd_adjust_trust(self, ctx: NexusContext):
        """Manually adjust trust score."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /adjusttrust @user <delta> [reason]")
            return

        # Parse arguments
        target_username = args[0].lstrip("@")
        try:
            delta = int(args[1])
        except ValueError:
            await ctx.reply("❌ Delta must be a number")
            return

        reason = " ".join(args[2:]) if len(args) > 2 else "Manual adjustment"

        # Resolve user
        from shared.models import User, Member

        result = ctx.db.execute(
            f"SELECT id FROM users WHERE username = '{target_username}' LIMIT 1"
        )
        row = result.fetchone()

        if not row:
            await ctx.reply(f"❌ User @{target_username} not found")
            return

        user_db_id = row[0]

        # Apply adjustment
        engine = TrustEngine(ctx.db)
        await engine.process_event(
            ctx.group.id,
            user_db_id,
            "admin_adjustment",
            {"delta": delta, "reason": reason},
        )

        # Get new score
        new_score = await engine.calculate_trust_score(ctx.group.id, user_db_id)

        await ctx.reply(
            f"✅ Trust score adjusted for @{target_username}\n"
            f"Change: {delta:+,}\n"
            f"New score: {new_score}/100\n"
            f"Reason: {reason}"
        )
