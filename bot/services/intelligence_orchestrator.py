"""Cross-Module Intelligence Orchestrator.

This is the core service that connects all Nexus modules through a unified
intelligence layer. It calculates composite scores that influence moderation
decisions, spotlight selection, challenge participation, and more.

The orchestrator ensures that trust score, XP, reputation, activity, and
economy all influence each other as described in the requirements.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    Group,
    Member,
    MemberBadge,
    ModAction,
    Reputation,
    Wallet,
)
from shared.models import MemberIntelligence, IntelligenceConfig


@dataclass
class MemberInfluenceProfile:
    """Complete influence profile for a member."""

    # Core identifiers
    user_id: int
    group_id: int

    # Individual module scores (0-100 normalized)
    trust_score: float
    xp_level: float  # Normalized XP (0-100)
    reputation_score: float
    activity_score: float
    economy_score: float
    badge_score: float

    # Composite influence scores (-1 to 1)
    moderation_influence: float  # Positive = more lenient, negative = stricter
    visibility_boost: float  # For spotlight/challenges
    privilege_level: int  # Calculated privilege tier

    # Tier classifications
    trust_tier: str  # trusted, neutral, suspicious
    engagement_tier: str  # high, average, low
    activity_tier: str  # very_active, regular, inactive

    # Recommended actions
    recommended_actions: List[str]

    # Contributing factors
    factors: Dict[str, float]


@dataclass
class ModerationContext:
    """Context for moderation decisions influenced by intelligence."""

    # Whether to apply leniency
    apply_leniency: bool

    # Threshold adjustments
    warn_threshold_modifier: float  # Multiplier for warn threshold
    mute_duration_modifier: float  # Multiplier for mute duration
    auto_approve: bool  # Skip moderation for trusted users

    # Required review level
    review_required: bool
    notify_admins: bool

    # Reasoning
    reasoning: List[str]


class IntelligenceOrchestrator:
    """Orchestrates cross-module intelligence calculations."""

    # Tier thresholds
    TRUST_TIERS = {
        "trusted": 80,
        "neutral": 50,
        "suspicious": 0,
    }

    ACTIVITY_TIERS = {
        "very_active": 80,
        "regular": 40,
        "inactive": 0,
    }

    ENGAGEMENT_TIERS = {
        "high": 75,
        "average": 40,
        "low": 0,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_member_intelligence(
        self,
        group_id: int,
        user_id: int,
        force_recalculate: bool = False,
    ) -> MemberInfluenceProfile:
        """Calculate complete intelligence profile for a member.

        This is the core method that computes cross-module influence scores
        based on all available member data.
        """
        # Check if we have a recent calculation
        if not force_recalculate:
            existing = await self._get_existing_intelligence(group_id, user_id)
            if existing and existing.calculated_at > datetime.utcnow() - timedelta(hours=1):
                return self._profile_from_db(existing)

        # Get group config
        config = await self._get_or_create_config(group_id)

        # Gather all module data
        member_data = await self._get_member_data(group_id, user_id)
        trust_data = await self._get_trust_context(group_id, user_id)
        reputation_data = await self._get_reputation_data(group_id, user_id)
        economy_data = await self._get_economy_data(group_id, user_id)
        activity_data = await self._get_activity_data(group_id, user_id)
        badge_data = await self._get_badge_data(group_id, user_id)

        # Calculate normalized scores (0-100)
        trust_normalized = member_data.get("trust_score", 50)
        xp_normalized = min(member_data.get("xp", 0) / 10, 100)  # 1000 XP = 100
        reputation_normalized = self._normalize_reputation(reputation_data)
        activity_normalized = activity_data.get("score", 50)
        economy_normalized = economy_data.get("score", 50)
        badge_normalized = badge_data.get("score", 50)

        # Calculate weighted composite scores
        factors = {
            "trust": trust_normalized * config.trust_weight,
            "xp": xp_normalized * config.xp_weight,
            "reputation": reputation_normalized * config.reputation_weight,
            "activity": activity_normalized * config.activity_weight,
            "economy": economy_normalized * config.economy_weight,
            "badge": badge_normalized * config.badge_weight,
        }

        # Moderation influence (-1 to 1)
        # Positive = trusted user, more leniency
        # Negative = problematic user, stricter moderation
        moderation_influence = self._calculate_moderation_influence(
            trust_normalized,
            reputation_normalized,
            member_data.get("warn_count", 0),
            member_data.get("mute_count", 0),
            member_data.get("ban_count", 0),
        )

        # Visibility boost (0 to 1)
        # Higher for engaged, positive community members
        visibility_boost = self._calculate_visibility_boost(
            activity_normalized,
            reputation_normalized,
            trust_normalized,
            badge_normalized,
        )

        # Privilege level (0-5)
        privilege_level = self._calculate_privilege_level(
            trust_normalized,
            xp_normalized,
            reputation_normalized,
            activity_normalized,
            member_data.get("role", "member"),
        )

        # Determine tiers
        trust_tier = self._get_trust_tier(trust_normalized)
        engagement_tier = self._get_engagement_tier(
            activity_normalized, reputation_normalized
        )
        activity_tier = self._get_activity_tier(activity_normalized)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            trust_tier,
            engagement_tier,
            activity_tier,
            member_data,
            moderation_influence,
        )

        # Create profile
        profile = MemberInfluenceProfile(
            user_id=user_id,
            group_id=group_id,
            trust_score=trust_normalized,
            xp_level=xp_normalized,
            reputation_score=reputation_normalized,
            activity_score=activity_normalized,
            economy_score=economy_normalized,
            badge_score=badge_normalized,
            moderation_influence=moderation_influence,
            visibility_boost=visibility_boost,
            privilege_level=privilege_level,
            trust_tier=trust_tier,
            engagement_tier=engagement_tier,
            activity_tier=activity_tier,
            recommended_actions=recommendations,
            factors=factors,
        )

        # Persist to database
        await self._persist_intelligence(profile, config)

        return profile

    async def get_moderation_context(
        self,
        group_id: int,
        user_id: int,
        action_type: str = "warn",
    ) -> ModerationContext:
        """Get moderation decision context influenced by intelligence.

        This is where the cross-module intelligence actually affects moderation.
        Trusted users get leniency, problematic users get stricter treatment.
        """
        profile = await self.calculate_member_intelligence(group_id, user_id)

        reasoning = []

        # Determine leniency
        apply_leniency = False
        if profile.trust_tier == "trusted" and profile.moderation_influence > 0.5:
            apply_leniency = True
            reasoning.append(f"Trusted user (score: {profile.trust_score:.0f})")

        if profile.engagement_tier == "high" and profile.reputation_score > 70:
            apply_leniency = True
            reasoning.append(f"High engagement with positive reputation")

        # Calculate threshold modifiers
        warn_threshold_modifier = 1.0
        mute_duration_modifier = 1.0
        auto_approve = False

        if apply_leniency:
            # Increase warn threshold (more warnings before action)
            warn_threshold_modifier = 1.5 + (profile.moderation_influence * 0.5)
            # Reduce mute duration
            mute_duration_modifier = max(0.3, 1.0 - profile.moderation_influence)

            # Auto-approve for very trusted users
            if profile.privilege_level >= 4 and profile.trust_score >= 90:
                auto_approve = True
                reasoning.append("Auto-approval enabled for high privilege")

        elif profile.trust_tier == "suspicious":
            # Stricter for suspicious users
            warn_threshold_modifier = 0.7
            mute_duration_modifier = 1.3
            reasoning.append(f"Suspicious user - stricter moderation applied")

        # Determine if review is required
        review_required = False
        if profile.privilege_level >= 3:
            # High privilege users need admin review for serious actions
            if action_type in ["ban", "mute"]:
                review_required = True
                reasoning.append("Review required due to user privilege level")

        # Always notify admins for suspicious users on serious actions
        notify_admins = profile.trust_tier == "suspicious" and action_type in [
            "ban",
            "mute",
        ]

        return ModerationContext(
            apply_leniency=apply_leniency,
            warn_threshold_modifier=warn_threshold_modifier,
            mute_duration_modifier=mute_duration_modifier,
            auto_approve=auto_approve,
            review_required=review_required,
            notify_admins=notify_admins,
            reasoning=reasoning,
        )

    async def get_spotlight_candidates(
        self,
        group_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get candidates for member spotlight based on intelligence.

        Considers activity, reputation, trust, and engagement to find
        standout community members.
        """
        config = await self._get_or_create_config(group_id)

        if not config.influence_spotlight:
            # Return basic candidates without intelligence weighting
            return await self._get_basic_candidates(group_id, limit)

        # Get all members with recent activity
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.message_count > 10,
                Member.is_banned == False,
            )
        )
        members = result.scalars().all()

        scored_candidates = []
        for member in members:
            profile = await self.calculate_member_intelligence(
                group_id, member.user_id
            )

            # Calculate spotlight score
            score = (
                profile.visibility_boost * 100
                + profile.activity_score * 0.3
                + profile.reputation_score * 0.2
                + profile.badge_score * 0.1
            )

            # Boost for diverse representation
            if profile.activity_tier == "very_active":
                score += 10

            scored_candidates.append(
                {
                    "user_id": member.user_id,
                    "score": score,
                    "profile": profile,
                    "reasons": self._get_spotlight_reasons(profile),
                }
            )

        # Sort by score and return top candidates
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:limit]

    async def get_challenge_participants(
        self,
        group_id: int,
        challenge_type: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get optimal challenge participants based on intelligence.

        Balances engagement levels to create inclusive challenges.
        """
        config = await self._get_or_create_config(group_id)

        if not config.influence_challenges:
            return await self._get_basic_candidates(group_id, limit)

        # Get members from different engagement tiers
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.is_banned == False,
            )
        )
        members = result.scalars().all()

        candidates = []
        tier_counts = {"high": 0, "average": 0, "low": 0}
        max_per_tier = limit // 3

        for member in members:
            profile = await self.calculate_member_intelligence(
                group_id, member.user_id
            )

            tier = profile.engagement_tier
            if tier_counts[tier] < max_per_tier:
                candidates.append(
                    {
                        "user_id": member.user_id,
                        "tier": tier,
                        "score": profile.visibility_boost * 100,
                        "profile": profile,
                    }
                )
                tier_counts[tier] += 1

            if len(candidates) >= limit:
                break

        return candidates

    def _normalize_reputation(self, rep_data: Dict) -> float:
        """Normalize reputation score to 0-100."""
        score = rep_data.get("score", 0)
        # Reputation can be negative, normalize to 0-100
        # Assuming range of -100 to +100
        return max(0, min(100, (score + 100) / 2))

    def _calculate_moderation_influence(
        self,
        trust: float,
        reputation: float,
        warns: int,
        mutes: int,
        bans: int,
    ) -> float:
        """Calculate moderation influence score (-1 to 1).

        Positive = trusted, gets leniency
        Negative = problematic, gets stricter moderation
        """
        # Start with trust and reputation
        influence = (trust / 100 * 0.4) + (reputation / 100 * 0.3)

        # Penalty for past infractions
        infraction_penalty = (warns * 0.05) + (mutes * 0.1) + (bans * 0.2)
        influence -= min(infraction_penalty, 0.7)  # Cap penalty

        return max(-1, min(1, influence))

    def _calculate_visibility_boost(
        self,
        activity: float,
        reputation: float,
        trust: float,
        badges: float,
    ) -> float:
        """Calculate visibility boost for spotlight/challenges (0 to 1)."""
        boost = (
            (activity / 100 * 0.3)
            + (reputation / 100 * 0.3)
            + (trust / 100 * 0.2)
            + (badges / 100 * 0.2)
        )
        return max(0, min(1, boost))

    def _calculate_privilege_level(
        self,
        trust: float,
        xp: float,
        reputation: float,
        activity: float,
        role: str,
    ) -> int:
        """Calculate privilege level (0-5) based on all factors."""
        score = (trust + xp + reputation + activity) / 4

        # Role bonus
        role_bonus = {"owner": 50, "admin": 40, "moderator": 30, "member": 0}
        score += role_bonus.get(role, 0)

        # Convert to level
        if score >= 90:
            return 5
        elif score >= 75:
            return 4
        elif score >= 60:
            return 3
        elif score >= 40:
            return 2
        elif score >= 20:
            return 1
        return 0

    def _get_trust_tier(self, trust_score: float) -> str:
        """Get trust tier from score."""
        if trust_score >= self.TRUST_TIERS["trusted"]:
            return "trusted"
        elif trust_score >= self.TRUST_TIERS["neutral"]:
            return "neutral"
        return "suspicious"

    def _get_activity_tier(self, activity_score: float) -> str:
        """Get activity tier from score."""
        if activity_score >= self.ACTIVITY_TIERS["very_active"]:
            return "very_active"
        elif activity_score >= self.ACTIVITY_TIERS["regular"]:
            return "regular"
        return "inactive"

    def _get_engagement_tier(self, activity: float, reputation: float) -> str:
        """Get engagement tier based on activity and reputation."""
        score = (activity * 0.6) + (reputation * 0.4)
        if score >= self.ENGAGEMENT_TIERS["high"]:
            return "high"
        elif score >= self.ENGAGEMENT_TIERS["average"]:
            return "average"
        return "low"

    def _generate_recommendations(
        self,
        trust_tier: str,
        engagement_tier: str,
        activity_tier: str,
        member_data: Dict,
        moderation_influence: float,
    ) -> List[str]:
        """Generate recommended actions based on profile."""
        recommendations = []

        if trust_tier == "suspicious":
            recommendations.append("increased_monitoring")
            recommendations.append("review_recent_actions")

        if engagement_tier == "low" and activity_tier == "inactive":
            recommendations.append("re_engagement_campaign")

        if trust_tier == "trusted" and engagement_tier == "high":
            recommendations.append("spotlight_candidate")
            recommendations.append("mentor_program")

        if moderation_influence < -0.5:
            recommendations.append("intervention_needed")

        if member_data.get("streak_days", 0) >= 30:
            recommendations.append("loyalty_reward")

        return recommendations

    def _get_spotlight_reasons(self, profile: MemberInfluenceProfile) -> List[str]:
        """Get human-readable reasons for spotlight candidacy."""
        reasons = []

        if profile.activity_tier == "very_active":
            reasons.append("Very active community member")

        if profile.reputation_score > 70:
            reasons.append("Positive community influence")

        if profile.badge_score > 60:
            reasons.append("Achieved multiple badges")

        if profile.trust_tier == "trusted":
            reasons.append("Highly trusted member")

        return reasons

    async def _get_existing_intelligence(
        self, group_id: int, user_id: int
    ) -> Optional[MemberIntelligence]:
        """Get existing intelligence record if available."""
        result = await self.db.execute(
            select(MemberIntelligence).where(
                MemberIntelligence.group_id == group_id,
                MemberIntelligence.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_config(self, group_id: int) -> IntelligenceConfig:
        """Get or create intelligence config for group."""
        result = await self.db.execute(
            select(IntelligenceConfig).where(
                IntelligenceConfig.group_id == group_id
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            config = IntelligenceConfig(
                group_id=group_id,
                enabled=True,
            )
            self.db.add(config)
            await self.db.flush()

        return config

    async def _get_member_data(self, group_id: int, user_id: int) -> Dict:
        """Get core member data."""
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            return {}

        return {
            "trust_score": member.trust_score,
            "xp": member.xp,
            "level": member.level,
            "warn_count": member.warn_count,
            "mute_count": member.mute_count,
            "ban_count": member.ban_count,
            "message_count": member.message_count,
            "streak_days": member.streak_days,
            "role": member.role,
            "joined_at": member.joined_at,
        }

    async def _get_trust_context(self, group_id: int, user_id: int) -> Dict:
        """Get trust-related context."""
        # Get recent trust history
        from shared.models import TrustScoreHistory

        result = await self.db.execute(
            select(TrustScoreHistory)
            .where(
                TrustScoreHistory.group_id == group_id,
                TrustScoreHistory.user_id == user_id,
            )
            .order_by(TrustScoreHistory.created_at.desc())
            .limit(10)
        )
        history = result.scalars().all()

        if not history:
            return {"trend": "stable", "recent_changes": 0}

        # Calculate trend
        recent_changes = sum(h.delta for h in history[:5])
        trend = "improving" if recent_changes > 5 else "declining" if recent_changes < -5 else "stable"

        return {
            "trend": trend,
            "recent_changes": recent_changes,
            "history_count": len(history),
        }

    async def _get_reputation_data(self, group_id: int, user_id: int) -> Dict:
        """Get reputation data."""
        result = await self.db.execute(
            select(Reputation).where(
                Reputation.group_id == group_id,
                Reputation.user_id == user_id,
            )
        )
        rep = result.scalar_one_or_none()

        return {"score": rep.score if rep else 0}

    async def _get_economy_data(self, group_id: int, user_id: int) -> Dict:
        """Get economy data and calculate score."""
        result = await self.db.execute(
            select(Wallet).where(
                Wallet.group_id == group_id,
                Wallet.user_id == user_id,
            )
        )
        wallet = result.scalar_one_or_none()

        if not wallet:
            return {"score": 0, "balance": 0}

        # Normalize balance to 0-100 (assuming 10k is max relevant)
        score = min(100, (wallet.balance / 10000) * 100)

        return {"score": score, "balance": wallet.balance}

    async def _get_activity_data(self, group_id: int, user_id: int) -> Dict:
        """Get activity data and calculate score."""
        # Get recent message count
        from datetime import datetime, timedelta

        from shared.models import Message

        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(Message)
            .where(
                Message.group_id == group_id,
                Message.user_id == user_id,
                Message.created_at > week_ago,
            )
            .count()
        )
        recent_messages = result.scalar()

        # Normalize to 0-100 (assuming 100 msgs/week is very active)
        score = min(100, recent_messages)

        return {"score": score, "recent_messages": recent_messages}

    async def _get_badge_data(self, group_id: int, user_id: int) -> Dict:
        """Get badge data."""
        # Get member ID first
        result = await self.db.execute(
            select(Member.id).where(
                Member.group_id == group_id,
                Member.user_id == user_id,
            )
        )
        member_id = result.scalar()

        if not member_id:
            return {"score": 0, "count": 0}

        # Count badges
        result = await self.db.execute(
            select(MemberBadge).where(MemberBadge.member_id == member_id)
        )
        badges = result.scalars().all()

        # Normalize to 0-100 (assuming 20 badges is max relevant)
        score = min(100, len(badges) * 5)

        return {"score": score, "count": len(badges)}

    async def _persist_intelligence(
        self, profile: MemberInfluenceProfile, config: IntelligenceConfig
    ):
        """Persist intelligence profile to database."""
        result = await self.db.execute(
            select(MemberIntelligence).where(
                MemberIntelligence.group_id == profile.group_id,
                MemberIntelligence.user_id == profile.user_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.calculated_at = datetime.utcnow()
            existing.trust_tier = profile.trust_tier
            existing.engagement_tier = profile.engagement_tier
            existing.reputation_tier = self._get_reputation_tier(profile.reputation_score)
            existing.activity_tier = profile.activity_tier
            existing.moderation_influence = profile.moderation_influence
            existing.visibility_boost = profile.visibility_boost
            existing.privilege_level = profile.privilege_level
            existing.factor_trust = profile.factors.get("trust", 0)
            existing.factor_xp = profile.factors.get("xp", 0)
            existing.factor_warnings = profile.factors.get("warnings", 0)
            existing.factor_streak = profile.factors.get("streak", 0)
            existing.factor_badges = profile.factors.get("badge", 0)
            existing.factor_reputation = profile.factors.get("reputation", 0)
            existing.factor_economy = profile.factors.get("economy", 0)
            existing.recommended_actions = profile.recommended_actions
        else:
            # Create new
            intelligence = MemberIntelligence(
                group_id=profile.group_id,
                user_id=profile.user_id,
                calculated_at=datetime.utcnow(),
                trust_tier=profile.trust_tier,
                engagement_tier=profile.engagement_tier,
                reputation_tier=self._get_reputation_tier(profile.reputation_score),
                activity_tier=profile.activity_tier,
                moderation_influence=profile.moderation_influence,
                visibility_boost=profile.visibility_boost,
                privilege_level=profile.privilege_level,
                factor_trust=profile.factors.get("trust", 0),
                factor_xp=profile.factors.get("xp", 0),
                factor_warnings=profile.factors.get("warnings", 0),
                factor_streak=profile.factors.get("streak", 0),
                factor_badges=profile.factors.get("badge", 0),
                factor_reputation=profile.factors.get("reputation", 0),
                factor_economy=profile.factors.get("economy", 0),
                recommended_actions=profile.recommended_actions,
            )
            self.db.add(intelligence)

        await self.db.flush()

    def _get_reputation_tier(self, score: float) -> str:
        """Get reputation tier from score."""
        if score >= 70:
            return "positive"
        elif score >= 40:
            return "neutral"
        return "negative"

    def _profile_from_db(self, db_record: MemberIntelligence) -> MemberInfluenceProfile:
        """Convert DB record to profile object."""
        return MemberInfluenceProfile(
            user_id=db_record.user_id,
            group_id=db_record.group_id,
            trust_score=db_record.factor_trust / 0.25 if db_record.factor_trust else 50,
            xp_level=db_record.factor_xp / 0.15 if db_record.factor_xp else 50,
            reputation_score=db_record.factor_reputation / 0.20 if db_record.factor_reputation else 50,
            activity_score=db_record.factor_streak / 0.20 if db_record.factor_streak else 50,
            economy_score=db_record.factor_economy / 0.10 if db_record.factor_economy else 50,
            badge_score=db_record.factor_badges / 0.10 if db_record.factor_badges else 50,
            moderation_influence=db_record.moderation_influence,
            visibility_boost=db_record.visibility_boost,
            privilege_level=db_record.privilege_level,
            trust_tier=db_record.trust_tier,
            engagement_tier=db_record.engagement_tier,
            activity_tier=db_record.activity_tier,
            recommended_actions=db_record.recommended_actions or [],
            factors={
                "trust": db_record.factor_trust,
                "xp": db_record.factor_xp,
                "reputation": db_record.factor_reputation,
                "activity": db_record.factor_streak,
                "economy": db_record.factor_economy,
                "badge": db_record.factor_badges,
            },
        )

    async def _get_basic_candidates(self, group_id: int, limit: int) -> List[Dict]:
        """Get basic candidates without intelligence weighting."""
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.message_count > 10,
            ).limit(limit)
        )
        members = result.scalars().all()

        return [
            {"user_id": m.user_id, "score": m.message_count, "profile": None}
            for m in members
        ]
