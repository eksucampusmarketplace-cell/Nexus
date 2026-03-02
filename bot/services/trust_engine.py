"""Trust Score System for Nexus.

Provides behavioral reputation scoring per member that influences:
- Moderation decisions (trusted users get leniency)
- Auto-approval for certain actions
- Badge eligibility
- Spotlight selection

Trust is built through positive contributions and eroded by violations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Member, TrustConfig, TrustScoreHistory


@dataclass
class TrustEvent:
    """A trust-affecting event."""
    event_type: str
    delta: int
    reason: str
    influencing_factors: Dict[str, Any]


@dataclass
class TrustReport:
    """Comprehensive trust report for a member."""
    user_id: int
    current_score: int
    previous_score: int
    score_change_7d: int
    score_change_30d: int
    tier: str  # trusted, neutral, suspicious
    events_recent: List[TrustEvent]
    contributing_factors: Dict[str, float]
    recommendations: List[str]


class TrustEngine:
    """Behavioral trust scoring engine."""

    # Default weights for trust calculation
    DEFAULT_WEIGHTS = {
        "message_quality": 0.20,
        "consistency": 0.15,
        "community_engagement": 0.20,
        "moderation_history": 0.25,
        "account_age": 0.10,
        "profile_completeness": 0.10,
    }

    # Tier thresholds
    TIERS = {
        "trusted": 80,
        "neutral": 50,
        "suspicious": 30,
        "untrusted": 0,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_trust_score(
        self,
        group_id: int,
        user_id: int,
        force_recalculate: bool = False,
    ) -> int:
        """Calculate trust score for a member.

        This is a comprehensive calculation based on multiple behavioral factors.
        """
        config = await self._get_config(group_id)

        # Get member data
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            return 50  # Default neutral score

        # Calculate component scores
        message_quality = await self._calculate_message_quality(member)
        consistency = await self._calculate_consistency(member)
        engagement = await self._calculate_engagement(member)
        mod_history = await self._calculate_moderation_factor(member)
        account_age = await self._calculate_account_age_factor(member)
        profile = await self._calculate_profile_factor(member)

        # Weighted composite score
        score = (
            message_quality * config.message_weight * 0.20
            + consistency * config.consistency_weight * 0.15
            + engagement * config.engagement_weight * 0.20
            + mod_history * config.moderation_weight * 0.25
            + account_age * 0.10
            + profile * 0.10
        )

        # Apply base score and clamp
        score = int(50 + score)  # Center around 50
        score = max(0, min(100, score))

        # Record history if significant change
        if abs(score - member.trust_score) >= 2 or force_recalculate:
            await self._record_trust_change(
                group_id, user_id, member.trust_score, score, "recalculation"
            )

            # Update member
            member.trust_score = score
            await self.db.flush()

        return score

    async def process_event(
        self,
        group_id: int,
        user_id: int,
        event_type: str,
        event_data: Optional[Dict] = None,
    ) -> TrustEvent:
        """Process a trust-affecting event.

        Events include: message_sent, report_received, warn_received,
        mute_received, ban_received, helpful_reaction, contribution_made, etc.
        """
        config = await self._get_config(group_id)
        event_data = event_data or {}

        # Determine delta based on event type and config
        delta = 0
        reason = ""
        factors = {}

        if event_type == "message_sent":
            # Small positive for active participation
            delta = 1
            reason = "Active participation"
            factors["activity"] = 1

        elif event_type == "quality_contribution":
            # Quality messages (longer, engagement)
            delta = config.quality_message_bonus
            reason = "Quality contribution"
            factors["quality"] = delta

        elif event_type == "helpful_reaction":
            # Receiving positive reactions
            delta = config.positive_reaction_bonus
            reason = "Community appreciation"
            factors["engagement"] = delta

        elif event_type == "report_received":
            # Being reported (not necessarily guilty)
            delta = config.report_penalty
            reason = "Report received"
            factors["violation"] = delta

        elif event_type == "warn_received":
            delta = config.warn_penalty
            reason = "Warning received"
            factors["moderation"] = delta

        elif event_type == "mute_received":
            delta = config.mute_penalty
            reason = "Mute received"
            factors["moderation"] = delta

        elif event_type == "ban_received":
            delta = config.ban_penalty
            reason = "Ban received"
            factors["moderation"] = delta

        elif event_type == "daily_streak":
            delta = config.daily_streak_bonus
            reason = f"{event_data.get('streak', 1)}-day activity streak"
            factors["consistency"] = delta

        elif event_type == "helpful_action":
            # Helping others, answering questions
            delta = config.helpful_action_bonus
            reason = "Helpful community action"
            factors["contribution"] = delta

        elif event_type == "violation_resolved":
            # Successfully appealing or resolving a violation
            delta = abs(config.warn_penalty) // 2
            reason = "Violation resolved positively"
            factors["recovery"] = delta

        elif event_type == "mentor_activity":
            # Helping new members
            delta = config.mentor_bonus
            reason = "Mentoring new members"
            factors["leadership"] = delta

        # Apply delta
        if delta != 0:
            await self._apply_trust_delta(
                group_id, user_id, delta, reason, factors
            )

        return TrustEvent(
            event_type=event_type,
            delta=delta,
            reason=reason,
            influencing_factors=factors,
        )

    async def get_trust_report(
        self, group_id: int, user_id: int
    ) -> TrustReport:
        """Get comprehensive trust report for a member."""
        # Get current member data
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Member not found")

        current_score = member.trust_score

        # Get historical data
        result = await self.db.execute(
            select(TrustScoreHistory)
            .where(
                TrustScoreHistory.group_id == group_id,
                TrustScoreHistory.user_id == user_id,
            )
            .order_by(TrustScoreHistory.created_at.desc())
            .limit(50)
        )
        history = result.scalars().all()

        # Calculate changes
        previous_score = history[0].old_score if history else current_score

        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)

        change_7d = sum(
            h.delta
            for h in history
            if h.created_at >= week_ago
        )

        change_30d = sum(
            h.delta
            for h in history
            if h.created_at >= month_ago
        )

        # Get recent events
        recent_events = [
            TrustEvent(
                event_type="trust_change",
                delta=h.delta,
                reason=h.reason,
                influencing_factors=h.influencing_factors or {},
            )
            for h in history[:10]
        ]

        # Determine tier
        tier = self._get_tier(current_score)

        # Calculate contributing factors
        factors = await self._calculate_contributing_factors(group_id, user_id, member)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            current_score, tier, change_7d, change_30d, factors
        )

        return TrustReport(
            user_id=user_id,
            current_score=current_score,
            previous_score=previous_score,
            score_change_7d=change_7d,
            score_change_30d=change_30d,
            tier=tier,
            events_recent=recent_events,
            contributing_factors=factors,
            recommendations=recommendations,
        )

    async def should_bypass_moderation(
        self, group_id: int, user_id: int, action_type: str = "general"
    ) -> Tuple[bool, str]:
        """Determine if user should bypass certain moderation checks.

        High trust users can bypass:
        - Anti-flood checks
        - Link verification
        - CAPTCHA
        - Slow mode
        """
        config = await self._get_config(group_id)

        result = await self.db.execute(
            select(Member.trust_score).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        trust_score = result.scalar() or 0

        # High trust bypass
        if trust_score >= config.high_trust_threshold:
            return True, f"High trust score ({trust_score}) - bypass enabled"

        # Medium trust partial bypass
        if trust_score >= config.medium_trust_threshold:
            if action_type in ["flood", "link"]:
                return True, f"Medium trust score ({trust_score}) - partial bypass"

        return False, f"Standard moderation (trust: {trust_score})"

    async def get_leaderboard(
        self, group_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get trust score leaderboard."""
        result = await self.db.execute(
            select(Member)
            .where(Member.group_id == group_id)
            .order_by(Member.trust_score.desc())
            .limit(limit)
        )
        members = result.scalars().all()

        leaderboard = []
        for i, member in enumerate(members, 1):
            leaderboard.append(
                {
                    "rank": i,
                    "user_id": member.user_id,
                    "trust_score": member.trust_score,
                    "tier": self._get_tier(member.trust_score),
                }
            )

        return leaderboard

    async def _get_config(self, group_id: int) -> TrustConfig:
        """Get or create trust config for group."""
        result = await self.db.execute(
            select(TrustConfig).where(TrustConfig.group_id == group_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = TrustConfig(
                group_id=group_id,
                enabled=True,
                message_weight=1.0,
                consistency_weight=1.0,
                engagement_weight=1.0,
                moderation_weight=1.0,
                quality_message_bonus=2,
                positive_reaction_bonus=1,
                report_penalty=-5,
                warn_penalty=-10,
                mute_penalty=-20,
                ban_penalty=-50,
                daily_streak_bonus=3,
                helpful_action_bonus=5,
                mentor_bonus=10,
                high_trust_threshold=80,
                medium_trust_threshold=60,
                low_trust_threshold=40,
            )
            self.db.add(config)
            await self.db.flush()

        return config

    async def _apply_trust_delta(
        self,
        group_id: int,
        user_id: int,
        delta: int,
        reason: str,
        factors: Dict[str, Any],
    ):
        """Apply a trust score delta."""
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            return

        old_score = member.trust_score
        new_score = max(0, min(100, old_score + delta))

        # Record the change
        await self._record_trust_change(
            group_id, user_id, old_score, new_score, reason, factors
        )

        # Update member
        member.trust_score = new_score
        await self.db.flush()

    async def _record_trust_change(
        self,
        group_id: int,
        user_id: int,
        old_score: int,
        new_score: int,
        reason: str,
        factors: Optional[Dict] = None,
    ):
        """Record a trust score change in history."""
        history = TrustScoreHistory(
            group_id=group_id,
            user_id=user_id,
            old_score=old_score,
            new_score=new_score,
            delta=new_score - old_score,
            reason=reason,
            influencing_factors=factors or {},
            created_at=datetime.utcnow(),
        )
        self.db.add(history)
        await self.db.flush()

    async def _calculate_message_quality(self, member: Member) -> float:
        """Calculate message quality score (0-100)."""
        # Factors: message length variety, engagement received, media sharing
        if member.message_count == 0:
            return 50

        # Base score on message count (more active = more data)
        base_score = min(70, member.message_count / 10)

        # Bonus for media sharing (visual content)
        media_ratio = member.media_count / max(member.message_count, 1)
        media_bonus = media_ratio * 20

        return base_score + media_bonus

    async def _calculate_consistency(self, member: Member) -> float:
        """Calculate activity consistency score (0-100)."""
        # Based on streak days and regular activity
        streak_score = min(50, member.streak_days * 2)

        # Time since join
        days_since_join = (datetime.utcnow() - member.joined_at).days
        if days_since_join > 0:
            consistency_ratio = member.streak_days / days_since_join
            consistency_score = consistency_ratio * 50
        else:
            consistency_score = 50

        return streak_score + consistency_score

    async def _calculate_engagement(self, member: Member) -> float:
        """Calculate community engagement score (0-100)."""
        # XP is a good proxy for engagement
        engagement_score = min(100, member.xp / 10)

        # Level bonus
        level_bonus = min(20, member.level)

        return engagement_score + level_bonus

    async def _calculate_moderation_factor(self, member: Member) -> float:
        """Calculate moderation history factor (0-100).

        Lower scores for members with violations.
        """
        violations = member.warn_count + member.mute_count * 2 + member.ban_count * 5

        # Exponential decay - early violations hurt more
        if violations == 0:
            return 100
        elif violations <= 2:
            return 80
        elif violations <= 5:
            return 60
        elif violations <= 10:
            return 40
        else:
            return 20

    async def _calculate_account_age_factor(self, member: Member) -> float:
        """Calculate account age factor (0-100)."""
        days_since_join = (datetime.utcnow() - member.joined_at).days

        # Linear growth for first 90 days, then plateau
        if days_since_join < 7:
            return 20
        elif days_since_join < 30:
            return 40
        elif days_since_join < 90:
            return 60
        else:
            return 80 + min(20, (days_since_join - 90) / 10)

    async def _calculate_profile_factor(self, member: Member) -> float:
        """Calculate profile completeness factor (0-100)."""
        score = 50  # Base score

        # Would check profile fields if we had more data
        # For now, use available indicators
        if member.custom_title:
            score += 20

        if member.xp > 100:
            score += 20

        if member.level > 5:
            score += 10

        return min(100, score)

    async def _calculate_contributing_factors(
        self, group_id: int, user_id: int, member: Member
    ) -> Dict[str, float]:
        """Calculate all contributing factor scores."""
        return {
            "message_quality": await self._calculate_message_quality(member),
            "consistency": await self._calculate_consistency(member),
            "engagement": await self._calculate_engagement(member),
            "moderation_history": await self._calculate_moderation_factor(member),
            "account_age": await self._calculate_account_age_factor(member),
            "profile": await self._calculate_profile_factor(member),
        }

    def _get_tier(self, score: int) -> str:
        """Get trust tier from score."""
        if score >= self.TIERS["trusted"]:
            return "trusted"
        elif score >= self.TIERS["neutral"]:
            return "neutral"
        elif score >= self.TIERS["suspicious"]:
            return "suspicious"
        return "untrusted"

    def _generate_recommendations(
        self,
        score: int,
        tier: str,
        change_7d: int,
        change_30d: int,
        factors: Dict[str, float],
    ) -> List[str]:
        """Generate trust improvement recommendations."""
        recommendations = []

        if tier == "trusted":
            recommendations.append("You're a trusted community member!")
            if change_7d < 0:
                recommendations.append("Your trust score dropped recently - review recent activity")

        elif tier == "neutral":
            recommendations.append("Keep participating regularly to build trust")
            if factors["consistency"] < 50:
                recommendations.append("Try to maintain daily activity for consistency")
            if factors["engagement"] < 50:
                recommendations.append("Engage more with the community to boost trust")

        elif tier == "suspicious":
            recommendations.append("Focus on positive contributions to rebuild trust")
            if factors["moderation_history"] < 50:
                recommendations.append("Avoid violations - each warning significantly impacts trust")
            if factors["consistency"] < 30:
                recommendations.append("Regular positive activity helps rebuild trust over time")

        if change_30d > 10:
            recommendations.append("Great progress! Your trust score improved significantly")
        elif change_30d < -10:
            recommendations.append("Your trust score declined - reach out to mods if concerned")

        return recommendations
