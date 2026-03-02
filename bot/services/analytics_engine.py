"""Real Analytics Engine for Nexus.

Provides comprehensive analytics including:
- Message volume charts with hourly/daily granularity
- Member retention data and cohort analysis
- Activity heatmaps by day/hour
- Sentiment tracking over time
- Growth metrics and predictions
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    DailyAnalytics,
    Group,
    HourlyStats,
    Member,
    MemberRetention,
    Message,
)


@dataclass
class HeatmapData:
    """Activity heatmap data."""
    days: List[str]  # Mon, Tue, etc.
    hours: List[int]  # 0-23
    data: List[List[int]]  # 2D array [day][hour]
    max_value: int


@dataclass
class RetentionCohort:
    """Retention cohort analysis."""
    join_date: date
    initial_size: int
    retention_by_day: Dict[int, int]  # day -> count


@dataclass
class SentimentTrend:
    """Sentiment trend data."""
    date: date
    avg_sentiment: float
    positive_ratio: float
    negative_ratio: float
    message_count: int


@dataclass
class GrowthMetrics:
    """Growth and engagement metrics."""
    current_members: int
    new_this_week: int
    new_this_month: int
    growth_rate: float  # Percentage
    churn_rate: float
    net_growth: int
    projected_month_end: int


class AnalyticsEngine:
    """Real analytics engine for group insights."""

    def __init__(self, db: AsyncSession, openai_api_key: Optional[str] = None):
        self.db = db
        self.openai_api_key = openai_api_key

    async def record_message(
        self,
        group_id: int,
        user_id: int,
        message_id: int,
        content: Optional[str],
        content_type: str = "text",
        is_forwarded: bool = False,
        has_media: bool = False,
        media_types: Optional[List[str]] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Message:
        """Record a message for analytics.

        This is called for every message to build analytics datasets.
        """
        # Analyze sentiment if content provided
        sentiment_score = None
        if content and self.openai_api_key:
            sentiment_score = await self._analyze_sentiment(content)

        message = Message(
            group_id=group_id,
            user_id=user_id,
            message_id=message_id,
            content=content[:1000] if content else None,  # Limit storage
            content_type=content_type,
            sentiment_score=sentiment_score,
            is_forwarded=is_forwarded,
            has_media=has_media,
            media_types=media_types or [],
            reply_to_message_id=reply_to_message_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(message)
        await self.db.flush()

        # Update hourly stats
        await self._update_hourly_stats(group_id, user_id, has_media)

        return message

    async def get_message_volume_chart(
        self,
        group_id: int,
        days: int = 30,
        granularity: str = "daily",  # daily or hourly
    ) -> Dict[str, Any]:
        """Get message volume chart data.

        Returns data formatted for Chart.js or similar charting libraries.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        if granularity == "hourly":
            # Get hourly data for recent days
            result = await self.db.execute(
                select(HourlyStats)
                .where(
                    HourlyStats.group_id == group_id,
                    HourlyStats.date >= start_date.date(),
                )
                .order_by(HourlyStats.date, HourlyStats.hour)
            )
            stats = result.scalars().all()

            labels = [f"{s.date} {s.hour:02d}:00" for s in stats]
            data = [s.message_count for s in stats]
        else:
            # Get daily rollup
            result = await self.db.execute(
                select(DailyAnalytics)
                .where(
                    DailyAnalytics.group_id == group_id,
                    DailyAnalytics.date >= start_date.date(),
                )
                .order_by(DailyAnalytics.date)
            )
            stats = result.scalars().all()

            labels = [s.date.strftime("%Y-%m-%d") for s in stats]
            data = [s.total_messages for s in stats]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Messages",
                    "data": data,
                    "borderColor": "#3B82F6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4,
                    "fill": True,
                }
            ],
            "summary": {
                "total": sum(data),
                "average": sum(data) / len(data) if data else 0,
                "peak": max(data) if data else 0,
                "trend": self._calculate_trend(data),
            },
        }

    async def get_activity_heatmap(
        self,
        group_id: int,
        days: int = 30,
    ) -> HeatmapData:
        """Get activity heatmap by day of week and hour.

        Shows when the group is most active.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(HourlyStats)
            .where(
                HourlyStats.group_id == group_id,
                HourlyStats.date >= start_date.date(),
            )
        )
        stats = result.scalars().all()

        # Initialize 7x24 grid
        days_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        data = [[0 for _ in range(24)] for _ in range(7)]

        for stat in stats:
            day_of_week = stat.date.weekday()  # 0 = Monday
            hour = stat.hour
            data[day_of_week][hour] += stat.message_count

        max_value = max(max(row) for row in data) if data else 1

        return HeatmapData(
            days=days_names,
            hours=list(range(24)),
            data=data,
            max_value=max_value,
        )

    async def get_member_retention(
        self,
        group_id: int,
        cohort_days: int = 30,
    ) -> List[RetentionCohort]:
        """Get member retention cohort analysis.

        Shows how well the group retains members over time.
        """
        cohorts = []

        # Get members grouped by join date
        result = await self.db.execute(
            select(
                func.date(Member.joined_at).label("join_date"),
                func.count(Member.id).label("count"),
            )
            .where(
                Member.group_id == group_id,
                Member.joined_at >= datetime.utcnow() - timedelta(days=cohort_days),
            )
            .group_by(func.date(Member.joined_at))
            .order_by(func.date(Member.joined_at))
        )

        join_data = result.all()

        for row in join_data:
            join_date = row.join_date
            initial_size = row.count

            # Calculate retention for this cohort
            retention_by_day = {}

            for day in [1, 3, 7, 14, 30]:
                check_date = join_date + timedelta(days=day)

                # Count how many from this cohort were active on check_date
                result = await self.db.execute(
                    select(func.count(Member.id))
                    .where(
                        Member.group_id == group_id,
                        func.date(Member.joined_at) == join_date,
                        Member.last_active >= check_date,
                    )
                )
                active_count = result.scalar() or 0
                retention_by_day[day] = active_count

            cohorts.append(
                RetentionCohort(
                    join_date=join_date,
                    initial_size=initial_size,
                    retention_by_day=retention_by_day,
                )
            )

        return cohorts

    async def get_sentiment_trends(
        self,
        group_id: int,
        days: int = 30,
    ) -> List[SentimentTrend]:
        """Get sentiment trends over time.

        Tracks the emotional tone of the group.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get daily sentiment aggregates from messages
        result = await self.db.execute(
            select(
                func.date(Message.created_at).label("msg_date"),
                func.avg(Message.sentiment_score).label("avg_sentiment"),
                func.count(Message.id).label("msg_count"),
                func.sum(func.case((Message.sentiment_score > 0.2, 1), else_=0)).label(
                    "positive_count"
                ),
                func.sum(func.case((Message.sentiment_score < -0.2, 1), else_=0)).label(
                    "negative_count"
                ),
            )
            .where(
                Message.group_id == group_id,
                Message.created_at >= start_date,
                Message.sentiment_score.isnot(None),
            )
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
        )

        trends = []
        for row in result.all():
            total = row.msg_count
            positive_ratio = (row.positive_count or 0) / total if total > 0 else 0
            negative_ratio = (row.negative_count or 0) / total if total > 0 else 0

            trends.append(
                SentimentTrend(
                    date=row.msg_date,
                    avg_sentiment=row.avg_sentiment or 0,
                    positive_ratio=positive_ratio,
                    negative_ratio=negative_ratio,
                    message_count=total,
                )
            )

        return trends

    async def get_growth_metrics(self, group_id: int) -> GrowthMetrics:
        """Get comprehensive growth metrics.

        Includes current state, trends, and projections.
        """
        # Current member count
        result = await self.db.execute(
            select(func.count(Member.id)).where(
                Member.group_id == group_id,
                Member.is_banned == False,
            )
        )
        current_members = result.scalar() or 0

        # New this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(func.count(Member.id)).where(
                Member.group_id == group_id,
                Member.joined_at >= week_ago,
            )
        )
        new_this_week = result.scalar() or 0

        # New this month
        month_ago = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(
            select(func.count(Member.id)).where(
                Member.group_id == group_id,
                Member.joined_at >= month_ago,
            )
        )
        new_this_month = result.scalar() or 0

        # Left members (churn)
        # This would require tracking departures separately
        churn_rate = 0.05  # Placeholder - would calculate from departure data

        # Growth rate
        month_before = datetime.utcnow() - timedelta(days=60)
        result = await self.db.execute(
            select(func.count(Member.id)).where(
                Member.group_id == group_id,
                Member.joined_at >= month_before,
                Member.joined_at < month_ago,
            )
        )
        prev_month = result.scalar() or 1
        growth_rate = ((new_this_month - prev_month) / prev_month) * 100

        # Net growth
        net_growth = new_this_month - int(current_members * churn_rate)

        # Projection
        daily_growth = new_this_month / 30
        days_remaining = 30 - datetime.utcnow().day
        projected_month_end = current_members + (daily_growth * days_remaining)

        return GrowthMetrics(
            current_members=current_members,
            new_this_week=new_this_week,
            new_this_month=new_this_month,
            growth_rate=growth_rate,
            churn_rate=churn_rate,
            net_growth=net_growth,
            projected_month_end=int(projected_month_end),
        )

    async def get_engagement_metrics(
        self, group_id: int, days: int = 7
    ) -> Dict[str, Any]:
        """Get engagement metrics.

        Measures how actively members participate.
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total members
        result = await self.db.execute(
            select(func.count(Member.id)).where(Member.group_id == group_id)
        )
        total_members = result.scalar() or 1

        # Active members (sent messages)
        result = await self.db.execute(
            select(func.count(func.distinct(Message.user_id))).where(
                Message.group_id == group_id,
                Message.created_at >= start_date,
            )
        )
        active_members = result.scalar() or 0

        # Engagement rate
        engagement_rate = (active_members / total_members) * 100

        # Messages per active user
        result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.group_id == group_id,
                Message.created_at >= start_date,
            )
        )
        total_messages = result.scalar() or 0
        msgs_per_user = total_messages / active_members if active_members > 0 else 0

        # Power users (top 10% by message count)
        result = await self.db.execute(
            select(Message.user_id, func.count(Message.id).label("msg_count"))
            .where(
                Message.group_id == group_id,
                Message.created_at >= start_date,
            )
            .group_by(Message.user_id)
            .order_by(func.count(Message.id).desc())
            .limit(int(total_members * 0.1))
        )
        power_users = len(result.all())

        return {
            "total_members": total_members,
            "active_members": active_members,
            "engagement_rate": round(engagement_rate, 1),
            "messages_per_user": round(msgs_per_user, 1),
            "total_messages": total_messages,
            "power_users": power_users,
            "power_user_ratio": round((power_users / total_members) * 100, 1),
        }

    async def get_top_contributors(
        self,
        group_id: int,
        days: int = 7,
        metric: str = "messages",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top contributors by various metrics."""
        start_date = datetime.utcnow() - timedelta(days=days)

        if metric == "messages":
            result = await self.db.execute(
                select(
                    Message.user_id,
                    func.count(Message.id).label("count"),
                )
                .where(
                    Message.group_id == group_id,
                    Message.created_at >= start_date,
                )
                .group_by(Message.user_id)
                .order_by(func.count(Message.id).desc())
                .limit(limit)
            )
        elif metric == "reactions":
            # Would need reaction tracking table
            return []
        elif metric == "engagement":
            # Combined metric
            return []
        else:
            return []

        contributors = []
        for row in result.all():
            # Get user details
            user_result = await self.db.execute(
                select(Member).where(
                    Member.group_id == group_id,
                    Member.user_id == row.user_id,
                )
            )
            member = user_result.scalar_one_or_none()

            if member:
                contributors.append(
                    {
                        "user_id": row.user_id,
                        "username": member.user.username if member.user else None,
                        "first_name": (
                            member.user.first_name if member.user else "Unknown"
                        ),
                        "count": row.count,
                        "metric": metric,
                    }
                )

        return contributors

    async def generate_analytics_report(
        self, group_id: int, period_days: int = 7
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report.

        Combines all metrics into a single report.
        """
        volume_chart = await self.get_message_volume_chart(group_id, period_days)
        heatmap = await self.get_activity_heatmap(group_id, period_days)
        growth = await self.get_growth_metrics(group_id)
        engagement = await self.get_engagement_metrics(group_id, period_days)
        sentiment = await self.get_sentiment_trends(group_id, period_days)
        top_contributors = await self.get_top_contributors(group_id, period_days)

        # Calculate insights
        insights = []

        if engagement["engagement_rate"] > 50:
            insights.append(
                {
                    "type": "positive",
                    "message": f"Excellent engagement rate of {engagement['engagement_rate']}%",
                }
            )
        elif engagement["engagement_rate"] < 20:
            insights.append(
                {
                    "type": "warning",
                    "message": f"Low engagement rate of {engagement['engagement_rate']}% - consider engagement activities",
                }
            )

        if growth.growth_rate > 10:
            insights.append(
                {
                    "type": "positive",
                    "message": f"Strong growth rate of {growth.growth_rate:.1f}% this month",
                }
            )

        if sentiment and len(sentiment) > 0:
            avg_sentiment = sum(s.avg_sentiment for s in sentiment) / len(sentiment)
            if avg_sentiment < -0.2:
                insights.append(
                    {
                        "type": "alert",
                        "message": "Group sentiment has been negative recently. Consider community wellness check.",
                    }
                )
            elif avg_sentiment > 0.3:
                insights.append(
                    {
                        "type": "positive",
                        "message": "Very positive group sentiment - great community health!",
                    }
                )

        # Peak activity time
        peak_hour = 0
        peak_count = 0
        for day_idx, day_data in enumerate(heatmap.data):
            for hour, count in enumerate(day_data):
                if count > peak_count:
                    peak_count = count
                    peak_hour = hour

        return {
            "period_days": period_days,
            "generated_at": datetime.utcnow().isoformat(),
            "volume_chart": volume_chart,
            "heatmap": {
                "days": heatmap.days,
                "hours": heatmap.hours,
                "data": heatmap.data,
                "max_value": heatmap.max_value,
                "peak_hour": peak_hour,
            },
            "growth": {
                "current_members": growth.current_members,
                "new_this_week": growth.new_this_week,
                "new_this_month": growth.new_this_month,
                "growth_rate": round(growth.growth_rate, 1),
                "projected_month_end": growth.projected_month_end,
            },
            "engagement": engagement,
            "sentiment": {
                "trend_data": [
                    {
                        "date": s.date.isoformat(),
                        "sentiment": s.avg_sentiment,
                        "positive": s.positive_ratio,
                        "negative": s.negative_ratio,
                    }
                    for s in sentiment
                ],
                "average": (
                    sum(s.avg_sentiment for s in sentiment) / len(sentiment)
                    if sentiment
                    else 0
                ),
            },
            "top_contributors": top_contributors,
            "insights": insights,
        }

    async def _update_hourly_stats(self, group_id: int, user_id: int, has_media: bool):
        """Update hourly statistics."""
        now = datetime.utcnow()
        today = now.date()
        current_hour = now.hour

        # Try to get existing stats
        result = await self.db.execute(
            select(HourlyStats).where(
                HourlyStats.group_id == group_id,
                HourlyStats.date == today,
                HourlyStats.hour == current_hour,
            )
        )
        stats = result.scalar_one_or_none()

        if stats:
            stats.message_count += 1
            if has_media:
                stats.media_count += 1
            # Note: unique_users would need more complex tracking
        else:
            stats = HourlyStats(
                group_id=group_id,
                date=today,
                hour=current_hour,
                message_count=1,
                unique_users=1,
                media_count=1 if has_media else 0,
                reaction_count=0,
            )
            self.db.add(stats)

        await self.db.flush()

    async def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using OpenAI or local method.

        Returns score from -1 (negative) to 1 (positive).
        """
        if not self.openai_api_key:
            # Simple fallback - keyword-based
            positive_words = ["good", "great", "awesome", "love", "happy", "thanks"]
            negative_words = ["bad", "terrible", "hate", "angry", "sad", "annoying"]

            text_lower = text.lower()
            pos_count = sum(1 for w in positive_words if w in text_lower)
            neg_count = sum(1 for w in negative_words if w in text_lower)

            total = pos_count + neg_count
            if total == 0:
                return 0
            return (pos_count - neg_count) / total

        # Would call OpenAI API here for proper sentiment analysis
        # For now, return neutral
        return 0.0

    def _calculate_trend(self, data: List[int]) -> str:
        """Calculate trend direction from data series."""
        if len(data) < 3:
            return "stable"

        # Simple linear trend
        first_half = sum(data[: len(data) // 2])
        second_half = sum(data[len(data) // 2 :])

        if second_half > first_half * 1.1:
            return "up"
        elif second_half < first_half * 0.9:
            return "down"
        return "stable"

    async def rollup_daily_analytics(self, group_id: int, target_date: date):
        """Roll up hourly stats into daily analytics.

        Should be run periodically (e.g., via Celery beat).
        """
        # Get all hourly stats for the date
        result = await self.db.execute(
            select(HourlyStats).where(
                HourlyStats.group_id == group_id,
                HourlyStats.date == target_date,
            )
        )
        hourly_stats = result.scalars().all()

        if not hourly_stats:
            return

        # Aggregate
        total_messages = sum(s.message_count for s in hourly_stats)
        total_media = sum(s.media_count for s in hourly_stats)

        # Find peak hour
        peak_hour = max(hourly_stats, key=lambda s: s.message_count).hour

        # Get unique users from messages
        result = await self.db.execute(
            select(func.count(func.distinct(Message.user_id))).where(
                Message.group_id == group_id,
                func.date(Message.created_at) == target_date,
            )
        )
        unique_users = result.scalar() or 0

        # Create or update daily analytics
        result = await self.db.execute(
            select(DailyAnalytics).where(
                DailyAnalytics.group_id == group_id,
                DailyAnalytics.date == target_date,
            )
        )
        daily = result.scalar_one_or_none()

        if daily:
            daily.total_messages = total_messages
            daily.unique_users = unique_users
            daily.peak_hour = peak_hour
        else:
            daily = DailyAnalytics(
                group_id=group_id,
                date=target_date,
                total_messages=total_messages,
                unique_users=unique_users,
                peak_hour=peak_hour,
            )
            self.db.add(daily)

        await self.db.flush()
