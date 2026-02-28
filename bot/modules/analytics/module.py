"""Analytics module - Group insights and analytics."""

from typing import Dict, List
from datetime import datetime, timedelta
from aiogram.types import Message
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class AnalyticsConfig(BaseModel):
    """Configuration for analytics module."""
    enabled: bool = True
    retention_days: int = 30


class AnalyticsModule(NexusModule):
    """Group analytics and insights."""

    name = "analytics"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Group insights and analytics dashboard"
    category = ModuleCategory.ANALYTICS

    config_schema = AnalyticsConfig
    default_config = AnalyticsConfig().dict()

    commands = [
        CommandDef(
            name="stats",
            description="View group statistics",
            admin_only=True,
        ),
        CommandDef(
            name="activity",
            description="View activity metrics",
            admin_only=True,
            args="[period]",
        ),
        CommandDef(
            name="members",
            description="View member statistics",
            admin_only=True,
        ),
        CommandDef(
            name="growth",
            description="View member growth chart",
            admin_only=True,
        ),
        CommandDef(
            name="heatmap",
            description="View activity heatmap",
            admin_only=True,
        ),
        CommandDef(
            name="top",
            description="View top members",
            admin_only=True,
            args="[metric]",
        ),
        CommandDef(
            name="trends",
            description="View message trends",
            admin_only=True,
        ),
        CommandDef(
            name="commands",
            description="View command usage stats",
            admin_only=True,
        ),
        CommandDef(
            name="moderation",
            description="View moderation statistics",
            admin_only=True,
        ),
        CommandDef(
            name="engagement",
            description="View engagement metrics",
            admin_only=True,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("stats", self.cmd_stats)
        self.register_command("activity", self.cmd_activity)
        self.register_command("members", self.cmd_members)
        self.register_command("growth", self.cmd_growth)
        self.register_command("heatmap", self.cmd_heatmap)
        self.register_command("top", self.cmd_top)
        self.register_command("trends", self.cmd_trends)
        self.register_command("commands", self.cmd_commands)
        self.register_command("moderation", self.cmd_moderation)
        self.register_command("engagement", self.cmd_engagement)

    async def cmd_stats(self, ctx: NexusContext):
        """View group statistics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            # Get various statistics
            from shared.models import Member

            # Total members
            total_members = ctx.db.execute(
                f"SELECT COUNT(*) FROM members WHERE group_id = {ctx.group.id}"
            ).scalar() or 0

            # Active members (messaged in last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            active_members = ctx.db.execute(
                f"""
                SELECT COUNT(DISTINCT user_id)
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND created_at > '{week_ago}'
                """
            ).scalar() or 0

            # Total messages
            total_messages = ctx.db.execute(
                f"SELECT COUNT(*) FROM messages WHERE group_id = {ctx.group.id}"
            ).scalar() or 0

            # Messages today
            today = datetime.now().date()
            messages_today = ctx.db.execute(
                f"""
                SELECT COUNT(*)
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND DATE(created_at) = '{today}'
                """
            ).scalar() or 0

            # Average messages per day
            days_active = 1  # Would calculate from first message
            avg_messages = total_messages // days_active if days_active else 0

            # Moderation actions
            mod_actions = ctx.db.execute(
                f"""
                SELECT COUNT(*)
                FROM mod_actions
                WHERE group_id = {ctx.group.id}
                """
            ).scalar() or 0

            stats_text = (
                f"📊 **Group Statistics**\n\n"
                f"🏠 Group: {ctx.group.title}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥 **Members**\n"
                f"• Total: {total_members}\n"
                f"• Active (7d): {active_members}\n"
                f"• Active Rate: {active_members * 100 // total_members if total_members else 0}%\n\n"
                f"💬 **Messages**\n"
                f"• Total: {total_messages:,}\n"
                f"• Today: {messages_today:,}\n"
                f"• Average/Day: {avg_messages:,}\n\n"
                f"🛡️ **Moderation**\n"
                f"• Actions Taken: {mod_actions}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📱 Open Mini App for detailed charts"
            )

            await ctx.reply(
                stats_text,
                buttons=[
                    [
                        {"text": "📱 Mini App", "url": f"https://t.me/{ctx.bot_username}?start=analytics"},
                        {"text": "📊 Detailed", "callback_data": "analytics_detailed"}
                    ]
                ]
            )

    async def cmd_activity(self, ctx: NexusContext):
        """View activity metrics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        period = (args[0].lower() if args else "day")

        # Calculate date range
        if period == "day":
            start = datetime.now() - timedelta(days=1)
        elif period == "week":
            start = datetime.now() - timedelta(days=7)
        elif period == "month":
            start = datetime.now() - timedelta(days=30)
        else:
            start = datetime.now() - timedelta(days=1)

        if ctx.db:
            # Messages per hour
            result = ctx.db.execute(
                f"""
                SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND created_at > '{start}'
                GROUP BY hour
                ORDER BY hour
                """
            )

            hourly = result.fetchall()

            # Create simple bar chart
            chart = "📊 **Activity by Hour**\n\n"
            for hour, count in hourly:
                bar = "█" * min(count // 10, 10)
                chart += f"{hour:02d}:00 {bar} {count}\n"

            await ctx.reply(chart)

    async def cmd_members(self, ctx: NexusContext):
        """View member statistics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import Member

            # Members by role
            roles = ctx.db.execute(
                f"""
                SELECT role, COUNT(*)
                FROM members
                WHERE group_id = {ctx.group.id}
                GROUP BY role
                """
            ).fetchall()

            # Members by level
            levels = ctx.db.execute(
                f"""
                SELECT level, COUNT(*)
                FROM members
                WHERE group_id = {ctx.group.id}
                GROUP BY level
                ORDER BY level DESC
                LIMIT 5
                """
            ).fetchall()

            # Trust score distribution
            trust_dist = ctx.db.execute(
                f"""
                SELECT
                    CASE
                        WHEN trust_score >= 80 THEN 'High'
                        WHEN trust_score >= 50 THEN 'Medium'
                        ELSE 'Low'
                    END as level,
                    COUNT(*)
                FROM members
                WHERE group_id = {ctx.group.id}
                GROUP BY level
                """
            ).fetchall()

            text = "👥 **Member Statistics**\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            text += "🎭 **By Role:**\n"
            for role, count in roles:
                text += f"• {role.title()}: {count}\n"

            text += "\n⭐ **Top Levels:**\n"
            for level, count in levels:
                text += f"• Level {level}: {count}\n"

            text += "\n✅ **Trust Distribution:**\n"
            for level, count in trust_dist:
                text += f"• {level}: {count}\n"

            await ctx.reply(text)

    async def cmd_growth(self, ctx: NexusContext):
        """View member growth chart."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            # Members joined in last 30 days
            result = ctx.db.execute(
                f"""
                SELECT DATE(joined_at) as date, COUNT(*) as count
                FROM members
                WHERE group_id = {ctx.group.id}
                AND joined_at > NOW() - INTERVAL '30 days'
                GROUP BY date
                ORDER BY date
                """
            ).fetchall()

            if not result:
                await ctx.reply("❌ No growth data available")
                return

            text = "📈 **Member Growth (30 days)**\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for date, count in result:
                bar = "█" * min(count, 20)
                text += f"{date}: {bar} +{count}\n"

            total = sum(count for _, count in result)
            text += f"\n📊 Total new members: {total}"

            await ctx.reply(text)

    async def cmd_heatmap(self, ctx: NexusContext):
        """View activity heatmap."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            # Messages by day of week and hour
            result = ctx.db.execute(
                f"""
                SELECT
                    EXTRACT(DOW FROM created_at) as dow,
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND created_at > NOW() - INTERVAL '7 days'
                GROUP BY dow, hour
                ORDER BY dow, hour
                """
            ).fetchall()

            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

            text = "📊 **Activity Heatmap (7 days)**\n\n"
            text += "Time |"
            for i in range(24):
                text += f"{i:2d} "
            text += "\n"

            for dow in range(7):
                text += f"{days[dow]:4s} |"
                for hour in range(24):
                    count = next((c for d, h, c in result if d == dow and h == hour), 0)
                    if count == 0:
                        text += " . "
                    elif count < 10:
                        text += " ░ "
                    elif count < 50:
                        text += " ▒ "
                    elif count < 100:
                        text += " ▓ "
                    else:
                        text += " █ "
                text += "\n"

            text += "\nLegend: .(0) ░(1-9) ▒(10-49) ▓(50-99) █(100+)"

            await ctx.reply(text)

    async def cmd_top(self, ctx: NexusContext):
        """View top members."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        args = ctx.message.text.split()[1:] if ctx.message.text else []
        metric = (args[0].lower() if args else "messages")

        if ctx.db:
            if metric == "messages":
                result = ctx.db.execute(
                    f"""
                    SELECT u.username, u.first_name, m.message_count
                    FROM members m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.group_id = {ctx.group.id}
                    ORDER BY m.message_count DESC
                    LIMIT 10
                    """
                ).fetchall()
                label = "Messages"
            elif metric == "xp":
                result = ctx.db.execute(
                    f"""
                    SELECT u.username, u.first_name, m.xp
                    FROM members m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.group_id = {ctx.group.id}
                    ORDER BY m.xp DESC
                    LIMIT 10
                    """
                ).fetchall()
                label = "XP"
            elif metric == "level":
                result = ctx.db.execute(
                    f"""
                    SELECT u.username, u.first_name, m.level
                    FROM members m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.group_id = {ctx.group.id}
                    ORDER BY m.level DESC, m.xp DESC
                    LIMIT 10
                    """
                ).fetchall()
                label = "Level"
            elif metric == "trust":
                result = ctx.db.execute(
                    f"""
                    SELECT u.username, u.first_name, m.trust_score
                    FROM members m
                    JOIN users u ON m.user_id = u.id
                    WHERE m.group_id = {ctx.group.id}
                    ORDER BY m.trust_score DESC
                    LIMIT 10
                    """
                ).fetchall()
                label = "Trust"
            else:
                await ctx.reply(
                    "❌ Invalid metric. Use: messages, xp, level, trust"
                )
                return

            text = f"🏆 **Top 10 Members** ({metric})\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, row in enumerate(result, 1):
                username = row[0] or f"{row[1]}"
                value = row[2]
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f" {i}."
                text += f"{medal} {username}: {value:,}\n"

            await ctx.reply(text)

    async def cmd_trends(self, ctx: NexusContext):
        """View message trends."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            # Last 7 days
            result = ctx.db.execute(
                f"""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND created_at > NOW() - INTERVAL '7 days'
                GROUP BY date
                ORDER BY date
                """
            ).fetchall()

            if not result:
                await ctx.reply("❌ No trend data available")
                return

            text = "📈 **Message Trends (7 days)**\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            for date, count in result:
                bar = "█" * min(count // 10, 20)
                text += f"{date}: {bar} {count:,}\n"

            await ctx.reply(text)

    async def cmd_commands(self, ctx: NexusContext):
        """View command usage stats."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            # Would need command tracking in DB
            text = (
                "📊 **Command Usage**\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Command tracking requires database schema update.\n\n"
                "💡 Enable command tracking in Mini App settings."
            )

            await ctx.reply(text)

    async def cmd_moderation(self, ctx: NexusContext):
        """View moderation statistics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            from shared.models import ModAction

            # Actions by type
            by_type = ctx.db.execute(
                f"""
                SELECT action_type, COUNT(*) as count
                FROM mod_actions
                WHERE group_id = {ctx.group.id}
                GROUP BY action_type
                ORDER BY count DESC
                """
            ).fetchall()

            # Actions by actor
            by_actor = ctx.db.execute(
                f"""
                SELECT u.username, u.first_name, COUNT(*) as count
                FROM mod_actions ma
                JOIN users u ON ma.actor_id = u.id
                WHERE ma.group_id = {ctx.group.id}
                GROUP BY u.id
                ORDER BY count DESC
                LIMIT 5
                """
            ).fetchall()

            # Recent actions
            recent = ctx.db.execute(
                f"""
                SELECT action_type, created_at
                FROM mod_actions
                WHERE group_id = {ctx.group.id}
                ORDER BY created_at DESC
                LIMIT 10
                """
            ).fetchall()

            text = "🛡️ **Moderation Statistics**\n\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n\n"

            text += "📊 **By Action Type:**\n"
            for action_type, count in by_type:
                text += f"• {action_type}: {count}\n"

            text += "\n👮 **Top Moderators:**\n"
            for username, first_name, count in by_actor:
                name = username or first_name
                text += f"• {name}: {count}\n"

            text += "\n🕐 **Recent Actions:**\n"
            for action_type, created_at in recent:
                text += f"• {action_type} - {created_at.strftime('%Y-%m-%d %H:%M')}\n"

            await ctx.reply(text)

    async def cmd_engagement(self, ctx: NexusContext):
        """View engagement metrics."""
        if not ctx.user.is_admin:
            await ctx.reply(ctx.i18n.t("no_permission"))
            return

        if ctx.db:
            # Unique users last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            unique_users = ctx.db.execute(
                f"""
                SELECT COUNT(DISTINCT user_id)
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND created_at > '{week_ago}'
                """
            ).scalar() or 0

            # Total members
            total_members = ctx.db.execute(
                f"SELECT COUNT(*) FROM members WHERE group_id = {ctx.group.id}"
            ).scalar() or 0

            # Engagement rate
            engagement_rate = (unique_users * 100 // total_members) if total_members else 0

            # Average messages per active user
            messages_week = ctx.db.execute(
                f"""
                SELECT COUNT(*)
                FROM messages
                WHERE group_id = {ctx.group.id}
                AND created_at > '{week_ago}'
                """
            ).scalar() or 0

            avg_per_user = messages_week // unique_users if unique_users else 0

            text = (
                f"📊 **Engagement Metrics**\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👥 **Active Users (7d):** {unique_users:,}\n"
                f"📈 **Engagement Rate:** {engagement_rate}%\n"
                f"💬 **Messages/User:** {avg_per_user}\n\n"
                f"🎯 **Insights:**\n"
            )

            if engagement_rate > 70:
                text += "✅ Excellent engagement! The community is very active.\n"
            elif engagement_rate > 40:
                text += "👍 Good engagement. Consider more interactive events.\n"
            elif engagement_rate > 20:
                text += "⚠️ Moderate engagement. Try boosting activity.\n"
            else:
                text += "❌ Low engagement. Consider re-engagement strategies.\n"

            await ctx.reply(text)
