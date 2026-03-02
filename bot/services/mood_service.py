"""Mood Tracking Service for Nexus.

Tracks group sentiment over time and alerts admins when:
- Mood has been negative for several days
- Sudden sentiment drops occur
- Unusual patterns in emotional tone

Provides insights into community health.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    Group,
    Message,
    MoodConfig,
    MoodSnapshot,
)


@dataclass
class MoodAlert:
    """Mood alert for admins."""
    alert_type: str  # negative_streak, sudden_drop, positive_trend
    severity: str  # info, warning, alert
    message: str
    data: Dict[str, Any]
    recommended_actions: List[str]


@dataclass
class MoodSummary:
    """Mood summary for a period."""
    period_start: date
    period_end: date
    avg_sentiment: float
    sentiment_trend: str  # improving, declining, stable
    mood_label: str  # positive, negative, neutral, mixed
    dominant_emotions: List[str]
    message_count: int
    alerts_triggered: List[MoodAlert]


class MoodService:
    """Group mood and sentiment tracking service."""

    # Sentiment thresholds
    POSITIVE_THRESHOLD = 0.2
    NEGATIVE_THRESHOLD = -0.2

    # Mood labels based on sentiment
    MOOD_LABELS = {
        "very_positive": (0.5, 1.0),
        "positive": (0.2, 0.5),
        "neutral": (-0.2, 0.2),
        "negative": (-0.5, -0.2),
        "very_negative": (-1.0, -0.5),
    }

    def __init__(self, db: AsyncSession, openai_api_key: Optional[str] = None):
        self.db = db
        self.openai_api_key = openai_api_key

    async def analyze_message_sentiment(
        self, message_content: str
    ) -> float:
        """Analyze sentiment of a single message.

        Returns score from -1 (very negative) to 1 (very positive).
        """
        if not message_content:
            return 0.0

        if not self.openai_api_key:
            # Fallback: simple keyword-based analysis
            return self._keyword_sentiment(message_content)

        # Would call OpenAI for proper sentiment analysis
        # For now, use keyword fallback
        return self._keyword_sentiment(message_content)

    async def record_sentiment(
        self,
        group_id: int,
        user_id: int,
        message_id: int,
        content: str,
        timestamp: Optional[datetime] = None,
    ) -> float:
        """Record sentiment for a message.

        Updates the message record with sentiment score.
        """
        sentiment = await self.analyze_message_sentiment(content)

        # Update message record
        result = await self.db.execute(
            select(Message).where(
                Message.group_id == group_id,
                Message.message_id == message_id,
            )
        )
        message = result.scalar_one_or_none()

        if message:
            message.sentiment_score = sentiment
            await self.db.flush()

        # Check if we need to create a new mood snapshot
        await self._update_mood_snapshot(group_id, timestamp)

        return sentiment

    async def get_mood_summary(
        self,
        group_id: int,
        days: int = 7,
    ) -> MoodSummary:
        """Get mood summary for a period."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        # Get mood snapshots for period
        result = await self.db.execute(
            select(MoodSnapshot)
            .where(
                MoodSnapshot.group_id == group_id,
                MoodSnapshot.period_start >= start_date,
            )
            .order_by(MoodSnapshot.period_start)
        )
        snapshots = result.scalars().all()

        if not snapshots:
            # Calculate from raw messages
            return await self._calculate_summary_from_messages(
                group_id, start_date, end_date
            )

        # Aggregate snapshot data
        avg_sentiment = sum(s.avg_sentiment for s in snapshots) / len(snapshots)

        # Determine trend
        if len(snapshots) >= 2:
            first_half = sum(s.avg_sentiment for s in snapshots[: len(snapshots) // 2])
            second_half = sum(s.avg_sentiment for s in snapshots[len(snapshots) // 2 :])
            if second_half > first_half * 1.1:
                trend = "improving"
            elif second_half < first_half * 0.9:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Determine mood label
        mood_label = self._sentiment_to_label(avg_sentiment)

        # Aggregate dominant emotions
        all_emotions = []
        for s in snapshots:
            all_emotions.extend(s.dominant_topics or [])
        dominant_emotions = list(set(all_emotions))[:5]

        # Total messages
        total_messages = sum(s.message_count for s in snapshots)

        # Check for alerts
        alerts = await self._check_mood_alerts(group_id, snapshots)

        return MoodSummary(
            period_start=start_date,
            period_end=end_date,
            avg_sentiment=avg_sentiment,
            sentiment_trend=trend,
            mood_label=mood_label,
            dominant_emotions=dominant_emotions,
            message_count=total_messages,
            alerts_triggered=alerts,
        )

    async def check_alerts(self, group_id: int) -> List[MoodAlert]:
        """Check for mood-related alerts."""
        config = await self._get_config(group_id)

        if not config.enabled:
            return []

        # Get recent snapshots
        days_back = config.alert_negative_streak_days
        start_date = datetime.utcnow() - timedelta(days=days_back)

        result = await self.db.execute(
            select(MoodSnapshot)
            .where(
                MoodSnapshot.group_id == group_id,
                MoodSnapshot.period_start >= start_date,
            )
            .order_by(MoodSnapshot.period_start.desc())
        )
        snapshots = result.scalars().all()

        return await self._check_mood_alerts(group_id, snapshots)

    async def get_mood_chart(
        self,
        group_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get mood data formatted for charting."""
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get daily sentiment data
        result = await self.db.execute(
            select(
                func.date(Message.created_at).label("msg_date"),
                func.avg(Message.sentiment_score).label("avg_sentiment"),
                func.count(Message.id).label("msg_count"),
            )
            .where(
                Message.group_id == group_id,
                Message.created_at >= start_date,
                Message.sentiment_score.isnot(None),
            )
            .group_by(func.date(Message.created_at))
            .order_by(func.date(Message.created_at))
        )

        data = result.all()

        labels = [str(row.msg_date) for row in data]
        sentiment_values = [round(row.avg_sentiment or 0, 3) for row in data]
        volume_values = [row.msg_count for row in data]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Sentiment",
                    "data": sentiment_values,
                    "borderColor": "#10B981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "yAxisID": "sentiment",
                    "tension": 0.4,
                },
                {
                    "label": "Message Volume",
                    "data": volume_values,
                    "borderColor": "#3B82F6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "yAxisID": "volume",
                    "type": "bar",
                },
            ],
            "options": {
                "scales": {
                    "sentiment": {
                        "min": -1,
                        "max": 1,
                        "title": {"display": True, "text": "Sentiment"},
                    },
                    "volume": {
                        "position": "right",
                        "title": {"display": True, "text": "Messages"},
                    },
                }
            },
        }

    async def generate_weekly_report(
        self, group_id: int
    ) -> Dict[str, Any]:
        """Generate weekly mood report."""
        summary = await self.get_mood_summary(group_id, days=7)
        chart = await self.get_mood_chart(group_id, days=7)

        # Get insights
        insights = []

        if summary.mood_label in ["negative", "very_negative"]:
            insights.append(
                {
                    "type": "warning",
                    "title": "Negative Mood Detected",
                    "message": "The group's mood has been negative this week. Consider checking in with the community.",
                }
            )
        elif summary.mood_label in ["positive", "very_positive"]:
            insights.append(
                {
                    "type": "positive",
                    "title": "Positive Vibes!",
                    "message": "The community is showing positive sentiment. Great job maintaining a healthy environment!",
                }
            )

        if summary.sentiment_trend == "declining":
            insights.append(
                {
                    "type": "alert",
                    "title": "Sentiment Declining",
                    "message": "The mood has been declining. Watch for conflicts or issues that may need moderation.",
                }
            )

        # Highlight days
        result = await self.db.execute(
            select(
                func.date(Message.created_at).label("msg_date"),
                func.avg(Message.sentiment_score).label("avg_sentiment"),
            )
            .where(
                Message.group_id == group_id,
                Message.created_at >= datetime.utcnow() - timedelta(days=7),
                Message.sentiment_score.isnot(None),
            )
            .group_by(func.date(Message.created_at))
            .order_by(func.avg(Message.sentiment_score).desc())
        )
        daily_sentiment = result.all()

        best_day = daily_sentiment[0] if daily_sentiment else None
        worst_day = daily_sentiment[-1] if daily_sentiment else None

        return {
            "period": "Last 7 days",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "average_sentiment": round(summary.avg_sentiment, 3),
                "mood_label": summary.mood_label,
                "trend": summary.sentiment_trend,
                "total_messages": summary.message_count,
            },
            "chart": chart,
            "highlights": {
                "best_day": {
                    "date": str(best_day.msg_date) if best_day else None,
                    "sentiment": round(best_day.avg_sentiment, 3) if best_day else None,
                },
                "worst_day": {
                    "date": str(worst_day.msg_date) if worst_day else None,
                    "sentiment": round(worst_day.avg_sentiment, 3)
                    if worst_day
                    else None,
                },
            },
            "insights": insights,
            "alerts": [
                {
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                }
                for alert in summary.alerts_triggered
            ],
        }

    async def _get_config(self, group_id: int) -> MoodConfig:
        """Get or create mood config."""
        result = await self.db.execute(
            select(MoodConfig).where(MoodConfig.group_id == group_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = MoodConfig(
                group_id=group_id,
                enabled=True,
                tracking_period_hours=24,
                alert_negative_streak_days=3,
                alert_threshold=-0.3,
                notify_admins=True,
                weekly_report=True,
            )
            self.db.add(config)
            await self.db.flush()

        return config

    async def _update_mood_snapshot(
        self,
        group_id: int,
        timestamp: Optional[datetime] = None,
    ):
        """Update or create mood snapshot for current period."""
        config = await self._get_config(group_id)
        timestamp = timestamp or datetime.utcnow()

        # Calculate period boundaries
        period_hours = config.tracking_period_hours
        period_start = timestamp.replace(
            hour=(timestamp.hour // period_hours) * period_hours,
            minute=0,
            second=0,
            microsecond=0,
        )
        period_end = period_start + timedelta(hours=period_hours)

        # Get messages in period
        result = await self.db.execute(
            select(
                func.avg(Message.sentiment_score).label("avg_sentiment"),
                func.count(Message.id).label("msg_count"),
                func.sum(
                    func.case((Message.sentiment_score > 0.2, 1), else_=0)
                ).label("positive_count"),
                func.sum(
                    func.case((Message.sentiment_score < -0.2, 1), else_=0)
                ).label("negative_count"),
            ).where(
                Message.group_id == group_id,
                Message.created_at >= period_start,
                Message.created_at < period_end,
                Message.sentiment_score.isnot(None),
            )
        )
        stats = result.one()

        if stats.msg_count == 0:
            return

        # Calculate ratios
        total = stats.msg_count
        positive_ratio = (stats.positive_count or 0) / total
        negative_ratio = (stats.negative_count or 0) / total
        neutral_ratio = 1 - positive_ratio - negative_ratio

        # Determine mood label
        avg_sentiment = stats.avg_sentiment or 0
        mood_label = self._sentiment_to_label(avg_sentiment)

        # Check for alert
        alert_triggered = False
        alert_reason = None

        if avg_sentiment < config.alert_threshold:
            alert_triggered = True
            alert_reason = f"Sentiment below threshold: {avg_sentiment:.2f}"

        # Create or update snapshot
        result = await self.db.execute(
            select(MoodSnapshot).where(
                MoodSnapshot.group_id == group_id,
                MoodSnapshot.period_start == period_start,
            )
        )
        snapshot = result.scalar_one_or_none()

        if snapshot:
            snapshot.avg_sentiment = avg_sentiment
            snapshot.positive_ratio = positive_ratio
            snapshot.negative_ratio = negative_ratio
            snapshot.neutral_ratio = neutral_ratio
            snapshot.mood_label = mood_label
            snapshot.message_count = total
            snapshot.alert_triggered = alert_triggered
            snapshot.alert_reason = alert_reason
        else:
            snapshot = MoodSnapshot(
                group_id=group_id,
                period_start=period_start,
                period_end=period_end,
                avg_sentiment=avg_sentiment,
                positive_ratio=positive_ratio,
                negative_ratio=negative_ratio,
                neutral_ratio=neutral_ratio,
                mood_label=mood_label,
                message_count=total,
                alert_triggered=alert_triggered,
                alert_reason=alert_reason,
            )
            self.db.add(snapshot)

        await self.db.flush()

    async def _check_mood_alerts(
        self, group_id: int, snapshots: List[MoodSnapshot]
    ) -> List[MoodAlert]:
        """Check for mood-related alerts."""
        config = await self._get_config(group_id)
        alerts = []

        if not snapshots:
            return alerts

        # Check for negative streak
        recent_negative = [
            s for s in snapshots[: config.alert_negative_streak_days]
            if s.avg_sentiment < config.alert_threshold
        ]

        if len(recent_negative) >= config.alert_negative_streak_days:
            avg_of_negative = sum(s.avg_sentiment for s in recent_negative) / len(
                recent_negative
            )
            alerts.append(
                MoodAlert(
                    alert_type="negative_streak",
                    severity="alert",
                    message=f"Group mood has been negative for {len(recent_negative)} days (avg: {avg_of_negative:.2f})",
                    data={
                        "days": len(recent_negative),
                        "average_sentiment": avg_of_negative,
                    },
                    recommended_actions=[
                        "Check for ongoing conflicts",
                        "Consider community wellness post",
                        "Review recent moderation actions",
                        "Engage with positive content",
                    ],
                )
            )

        # Check for sudden drop
        if len(snapshots) >= 3:
            recent_avg = sum(s.avg_sentiment for s in snapshots[:3]) / 3
            previous_avg = sum(s.avg_sentiment for s in snapshots[3:6]) / 3

            if previous_avg > 0.1 and recent_avg < -0.2:
                drop = previous_avg - recent_avg
                alerts.append(
                    MoodAlert(
                        alert_type="sudden_drop",
                        severity="warning",
                        message=f"Sudden mood drop detected: {drop:.2f} change",
                        data={
                            "previous_avg": previous_avg,
                            "recent_avg": recent_avg,
                            "drop": drop,
                        },
                        recommended_actions=[
                            "Identify triggering events",
                            "Check for spam or raids",
                            "Review flagged messages",
                        ],
                    )
                )

        # Check for positive trend
        if len(snapshots) >= 7:
            week_avg = sum(s.avg_sentiment for s in snapshots[:7]) / 7
            if week_avg > 0.3:
                alerts.append(
                    MoodAlert(
                        alert_type="positive_trend",
                        severity="info",
                        message=f"Positive mood trend: {week_avg:.2f} average over last week",
                        data={"week_average": week_avg},
                        recommended_actions=[
                            "Celebrate the positive vibe!",
                            "Recognize contributing members",
                            "Share community wins",
                        ],
                    )
                )

        return alerts

    async def _calculate_summary_from_messages(
        self,
        group_id: int,
        start_date: date,
        end_date: date,
    ) -> MoodSummary:
        """Calculate summary directly from messages if no snapshots."""
        result = await self.db.execute(
            select(
                func.avg(Message.sentiment_score).label("avg_sentiment"),
                func.count(Message.id).label("msg_count"),
                func.sum(
                    func.case((Message.sentiment_score > 0.2, 1), else_=0)
                ).label("positive_count"),
                func.sum(
                    func.case((Message.sentiment_score < -0.2, 1), else_=0)
                ).label("negative_count"),
            ).where(
                Message.group_id == group_id,
                func.date(Message.created_at) >= start_date,
                func.date(Message.created_at) <= end_date,
                Message.sentiment_score.isnot(None),
            )
        )
        stats = result.one()

        avg_sentiment = stats.avg_sentiment or 0
        mood_label = self._sentiment_to_label(avg_sentiment)

        return MoodSummary(
            period_start=start_date,
            period_end=end_date,
            avg_sentiment=avg_sentiment,
            sentiment_trend="stable",
            mood_label=mood_label,
            dominant_emotions=[],
            message_count=stats.msg_count or 0,
            alerts_triggered=[],
        )

    def _keyword_sentiment(self, content: str) -> float:
        """Simple keyword-based sentiment analysis."""
        content_lower = content.lower()

        positive_words = [
            "good", "great", "awesome", "love", "happy", "thanks", "amazing",
            "excellent", "fantastic", "wonderful", "best", "perfect", "nice",
            "cool", "fun", "helpful", "appreciate", "grateful", "yes", "agree"
        ]

        negative_words = [
            "bad", "terrible", "awful", "hate", "angry", "sad", "annoying",
            "stupid", "worst", "horrible", "disgusting", "wrong", "no",
            "disagree", "disappointed", "frustrated", "upset", "mad"
        ]

        pos_count = sum(1 for word in positive_words if word in content_lower)
        neg_count = sum(1 for word in negative_words if word in content_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _sentiment_to_label(self, sentiment: float) -> str:
        """Convert sentiment score to mood label."""
        for label, (min_val, max_val) in self.MOOD_LABELS.items():
            if min_val <= sentiment <= max_val:
                return label
        return "neutral"
