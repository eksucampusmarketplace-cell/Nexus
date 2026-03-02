"""Advanced Analytics Module for Nexus.

Provides comprehensive group analytics including:
- Real-time message volume charts
- Member retention data and cohort analysis
- Activity heatmaps by day/hour
- Sentiment tracking and mood analysis
- Growth metrics and predictions
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule
from bot.services.analytics_engine import AnalyticsEngine


class AnalyticsConfig(BaseModel):
    """Configuration for analytics module."""
    enabled: bool = True
    track_messages: bool = True
    track_sentiment: bool = True
    retention_analysis: bool = True
    heatmap_enabled: bool = True
    public_stats: bool = False


class AdvancedAnalyticsModule(NexusModule):
    """Advanced group analytics and insights."""

    name = "advanced_analytics"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Real-time analytics with message volume, retention, heatmaps, and sentiment tracking"
    category = ModuleCategory.UTILITY

    config_schema = AnalyticsConfig
    default_config = AnalyticsConfig().dict()

    commands = [
        CommandDef(
            name="analytics",
            description="View comprehensive analytics dashboard",
            admin_only=True,
            aliases=["dashboard"],
        ),
        CommandDef(
            name="retention",
            description="View member retention analysis",
            admin_only=True,
        ),
        CommandDef(
            name="heatmap",
            description="View activity heatmap",
            admin_only=True,
        ),
        CommandDef(
            name="sentiment",
            description="View sentiment analysis",
            admin_only=True,
        ),
        CommandDef(
            name="growth",
            description="View growth metrics and projections",
            admin_only=True,
        ),
        CommandDef(
            name="engagement",
            description="View engagement metrics",
            admin_only=True,
        ),
        CommandDef(
            name="exportanalytics",
            description="Export analytics data",
            admin_only=True,
            args="[format]",
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("analytics", self.cmd_analytics)
        self.register_command("dashboard", self.cmd_analytics)
        self.register_command("retention", self.cmd_retention)
        self.register_command("heatmap", self.cmd_heatmap)
        self.register_command("sentiment", self.cmd_sentiment)
        self.register_command("growth", self.cmd_growth)
        self.register_command("engagement", self.cmd_engagement)
        self.register_command("exportanalytics", self.cmd_export_analytics)

    async def on_message(self, ctx: NexusContext) -> bool:
        """Track message for analytics."""
        config = AnalyticsConfig(**ctx.group.module_configs.get("advanced_analytics", {}))

        if not config.enabled or not config.track_messages:
            return False

        if not ctx.message:
            return False

        # Initialize analytics engine
        engine = AnalyticsEngine(ctx.db)

        # Determine content type
        content_type = "text"
        has_media = False
        media_types = []

        if ctx.message.photo:
            content_type = "photo"
            has_media = True
            media_types.append("photo")
        elif ctx.message.video:
            content_type = "video"
            has_media = True
            media_types.append("video")
        elif ctx.message.document:
            content_type = "document"
            has_media = True
            media_types.append("document")
        elif ctx.message.sticker:
            content_type = "sticker"
            has_media = True
            media_types.append("sticker")
        elif ctx.message.voice:
            content_type = "voice"
            has_media = True
            media_types.append("voice")

        # Record message
        await engine.record_message(
            group_id=ctx.group.id,
            user_id=ctx.user.user_id,
            message_id=ctx.message.message_id,
            content=ctx.message.text or ctx.message.caption,
            content_type=content_type,
            is_forwarded=ctx.message.forward_date is not None,
            has_media=has_media,
            media_types=media_types,
            reply_to_message_id=(
                ctx.message.reply_to_message.message_id
                if ctx.message.reply_to_message
                else None
            ),
        )

        # Analyze sentiment if enabled
        if config.track_sentiment and (ctx.message.text or ctx.message.caption):
            await engine.record_sentiment(
                group_id=ctx.group.id,
                user_id=ctx.user.user_id,
                message_id=ctx.message.message_id,
                content=ctx.message.text or ctx.message.caption,
            )

        return False

    async def cmd_analytics(self, ctx: NexusContext):
        """Show comprehensive analytics dashboard."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        engine = AnalyticsEngine(ctx.db)

        # Get quick stats
        growth = await engine.get_growth_metrics(ctx.group.id)
        engagement = await engine.get_engagement_metrics(ctx.group.id, days=7)

        text = (
            f"📊 **Analytics Dashboard**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 **Members**\n"
            f"• Total: {growth.current_members:,}\n"
            f"• New this week: +{growth.new_this_week}\n"
            f"• Growth rate: {growth.growth_rate:.1f}%\n\n"
            f"💬 **Engagement (7 days)**\n"
            f"• Active members: {engagement['active_members']}\n"
            f"• Engagement rate: {engagement['engagement_rate']}%\n"
            f"• Messages: {engagement['total_messages']:,}\n"
            f"• Avg per user: {engagement['messages_per_user']:.1f}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 **Commands**\n"
            f"/retention - Member retention\n"
            f"/heatmap - Activity patterns\n"
            f"/sentiment - Mood analysis\n"
            f"/growth - Growth metrics\n\n"
            f"📱 Open Mini App for detailed charts"
        )

        await ctx.reply(
            text,
            buttons=[
                [
                    {"text": "📊 Mini App", "url": f"https://t.me/{ctx.bot_username}?start=analytics"},
                    {"text": "📈 Charts", "callback_data": "analytics_charts"},
                ]
            ],
        )

    async def cmd_retention(self, ctx: NexusContext):
        """Show member retention analysis."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        engine = AnalyticsEngine(ctx.db)
        cohorts = await engine.get_member_retention(ctx.group.id, cohort_days=14)

        if not cohorts:
            await ctx.reply("❌ Not enough retention data yet. Check back in a few days.")
            return

        text = "📈 **Member Retention Analysis**\n\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"

        for cohort in cohorts[:5]:  # Show last 5 cohorts
            text += f"**Joined {cohort.join_date}** ({cohort.initial_size} members)\n"

            # Retention percentages
            for day in [1, 7, 14]:
                if day in cohort.retention_by_day:
                    count = cohort.retention_by_day[day]
                    pct = (count / cohort.initial_size * 100) if cohort.initial_size > 0 else 0
                    bar = "█" * int(pct / 10)
                    text += f"  Day {day}: {bar} {pct:.0f}% ({count})\n"

            text += "\n"

        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "Retention shows what % of new members stay active"

        await ctx.reply(text)

    async def cmd_heatmap(self, ctx: NexusContext):
        """Show activity heatmap."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        engine = AnalyticsEngine(ctx.db)
        heatmap = await engine.get_activity_heatmap(ctx.group.id, days=14)

        # Build text-based heatmap
        text = "📊 **Activity Heatmap** (Last 14 days)\n\n"
        text += "Hour | Activity by Day\n"
        text += "     | Mon Tue Wed Thu Fri Sat Sun\n"
        text += "━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        for hour in range(0, 24, 3):  # Every 3 hours
            text += f"{hour:02d}:00│ "
            for day_idx in range(7):
                count = heatmap.data[day_idx][hour]
                if count == 0:
                    text += "·   "
                elif count < heatmap.max_value * 0.25:
                    text += "░   "
                elif count < heatmap.max_value * 0.5:
                    text += "▒   "
                elif count < heatmap.max_value * 0.75:
                    text += "▓   "
                else:
                    text += "█   "
            text += "\n"

        text += "\nLegend: ·(none) ░(low) ▒(med) ▓(high) █(peak)"

        # Find peak time
        max_val = 0
        peak_day = 0
        peak_hour = 0
        for day_idx, day_data in enumerate(heatmap.data):
            for hour, count in enumerate(day_data):
                if count > max_val:
                    max_val = count
                    peak_day = day_idx
                    peak_hour = hour

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        text += f"\n\n🔥 Peak activity: {days[peak_day]} at {peak_hour:02d}:00"

        await ctx.reply(text)

    async def cmd_sentiment(self, ctx: NexusContext):
        """Show sentiment analysis."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        engine = AnalyticsEngine(ctx.db)
        trends = await engine.get_sentiment_trends(ctx.group.id, days=7)

        if not trends:
            await ctx.reply("❌ Not enough sentiment data yet. Sentiment tracking is active and collecting data.")
            return

        # Calculate averages
        avg_sentiment = sum(t.avg_sentiment for t in trends) / len(trends)
        avg_positive = sum(t.positive_ratio for t in trends) / len(trends)
        avg_negative = sum(t.negative_ratio for t in trends) / len(trends)

        # Mood emoji
        if avg_sentiment > 0.3:
            mood_emoji = "😊"
            mood_text = "Very Positive"
        elif avg_sentiment > 0.1:
            mood_emoji = "🙂"
            mood_text = "Positive"
        elif avg_sentiment > -0.1:
            mood_emoji = "😐"
            mood_text = "Neutral"
        elif avg_sentiment > -0.3:
            mood_emoji = "😕"
            mood_text = "Negative"
        else:
            mood_emoji = "😟"
            mood_text = "Very Negative"

        text = (
            f"{mood_emoji} **Sentiment Analysis** (Last 7 days)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Overall Mood: **{mood_text}**\n"
            f"Average Score: {avg_sentiment:.2f}/1.0\n\n"
            f"📊 **Breakdown**\n"
            f"😊 Positive: {avg_positive*100:.1f}%\n"
            f"😐 Neutral: {(1-avg_positive-avg_negative)*100:.1f}%\n"
            f"😟 Negative: {avg_negative*100:.1f}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )

        # Trend
        if len(trends) >= 2:
            recent = sum(t.avg_sentiment for t in trends[-3:]) / 3
            older = sum(t.avg_sentiment for t in trends[:3]) / 3

            if recent > older * 1.1:
                text += "📈 Trend: Improving 📈"
            elif recent < older * 0.9:
                text += "📉 Trend: Declining 📉"
            else:
                text += "➡️ Trend: Stable"

        await ctx.reply(text)

    async def cmd_growth(self, ctx: NexusContext):
        """Show growth metrics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        engine = AnalyticsEngine(ctx.db)
        metrics = await engine.get_growth_metrics(ctx.group.id)

        text = (
            f"📈 **Growth Metrics**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 **Current Members**: {metrics.current_members:,}\n\n"
            f"📊 **New Members**\n"
            f"• This week: +{metrics.new_this_week}\n"
            f"• This month: +{metrics.new_this_month}\n\n"
            f"📈 **Growth Rate**: {metrics.growth_rate:.1f}%\n"
            f"📉 **Churn Rate**: {metrics.churn_rate*100:.1f}%\n"
            f"🎯 **Net Growth**: {metrics.net_growth:+,}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔮 **Projection**: ~{metrics.projected_month_end:,} by month end"
        )

        # Growth assessment
        if metrics.growth_rate > 20:
            text += "\n\n🚀 **Excellent growth!** Your community is thriving!"
        elif metrics.growth_rate > 10:
            text += "\n\n👍 **Good growth** - keep up the momentum!"
        elif metrics.growth_rate > 0:
            text += "\n\n⚡ **Steady growth** - consider engagement activities"
        else:
            text += "\n\n⚠️ **Negative growth** - review retention strategies"

        await ctx.reply(text)

    async def cmd_engagement(self, ctx: NexusContext):
        """Show engagement metrics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        engine = AnalyticsEngine(ctx.db)
        metrics = await engine.get_engagement_metrics(ctx.group.id, days=7)

        # Engagement assessment
        if metrics['engagement_rate'] >= 50:
            assessment = "🌟 Excellent"
        elif metrics['engagement_rate'] >= 30:
            assessment = "👍 Good"
        elif metrics['engagement_rate'] >= 15:
            assessment = "⚡ Average"
        else:
            assessment = "⚠️ Needs Attention"

        text = (
            f"💬 **Engagement Metrics** (7 days)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 **Active Members**: {metrics['active_members']:,} / {metrics['total_members']:,}\n"
            f"📊 **Engagement Rate**: {metrics['engagement_rate']}%\n"
            f"💬 **Total Messages**: {metrics['total_messages']:,}\n"
            f"📈 **Msgs/User**: {metrics['messages_per_user']:.1f}\n\n"
            f"🌟 **Power Users**: {metrics['power_users']} ({metrics['power_user_ratio']}%)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Assessment: **{assessment}**"
        )

        await ctx.reply(text)

    async def cmd_export_analytics(self, ctx: NexusContext):
        """Export analytics data."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        await ctx.reply(
            "📤 **Export Analytics**\n\n"
            "Available exports:\n"
            "• `/exportanalytics json` - Full JSON export\n"
            "• `/exportanalytics csv` - CSV format\n"
            "• `/exportanalytics report` - PDF report (weekly)\n\n"
            "The export will include all analytics data for this group."
        )
