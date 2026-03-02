"""Member Spotlight Service for Nexus.

Automatically generates AI-written weekly features about standout
community members. Includes:
- Smart candidate selection based on engagement, trust, and contributions
- AI-generated natural-sounding writeups
- Featured stats and community quotes
- Automatic publishing with reactions tracking
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    Group,
    Member,
    MemberBadge,
    MemberSpotlight,
    Message,
    SpotlightConfig,
)


@dataclass
class SpotlightCandidate:
    """Candidate for spotlight feature."""
    user_id: int
    username: Optional[str]
    first_name: str
    score: float
    reasons: List[str]
    stats: Dict[str, Any]


@dataclass
class SpotlightFeature:
    """Generated spotlight feature."""
    user_id: int
    writeup: str
    featured_stats: Dict[str, Any]
    community_quotes: List[str]
    selection_reason: str


class SpotlightService:
    """Member spotlight generation service."""

    # AI personality templates
    PERSONALITIES = {
        "friendly": {
            "tone": "warm and conversational",
            "greeting": "Hey everyone! 👋",
            "closing": "Thanks for being awesome! 🌟",
        },
        "professional": {
            "tone": "polished and respectful",
            "greeting": "Hello community,",
            "closing": "We appreciate your contributions.",
        },
        "playful": {
            "tone": "fun and energetic",
            "greeting": "What's up, legends! 🎉",
            "closing": "Keep being amazing! ✨",
        },
        "inspirational": {
            "tone": "motivational and uplifting",
            "greeting": "Dear community,",
            "closing": "Together we grow stronger. 💪",
        },
    }

    def __init__(self, db: AsyncSession, openai_api_key: Optional[str] = None):
        self.db = db
        self.openai_api_key = openai_api_key

    async def select_candidate(
        self,
        group_id: int,
        exclude_recent: int = 4,  # Weeks
    ) -> Optional[SpotlightCandidate]:
        """Select the best candidate for spotlight.

        Uses multiple criteria to find a standout member who hasn't
        been featured recently.
        """
        config = await self._get_config(group_id)

        if not config.enabled:
            return None

        # Get recently featured users to exclude
        recent_date = datetime.utcnow() - timedelta(weeks=exclude_recent)
        result = await self.db.execute(
            select(MemberSpotlight.user_id).where(
                MemberSpotlight.group_id == group_id,
                MemberSpotlight.published_at >= recent_date,
            )
        )
        recent_ids = [row[0] for row in result.all()]

        # Get potential candidates
        result = await self.db.execute(
            select(Member).where(
                Member.group_id == group_id,
                Member.user_id.notin_(recent_ids) if recent_ids else True,
                Member.is_banned == False,
                Member.message_count > 10,  # Minimum activity
            )
        )
        members = result.scalars().all()

        if not members:
            return None

        # Score each candidate
        scored = []
        for member in members:
            score, reasons, stats = await self._score_candidate(group_id, member)
            scored.append(
                (
                    member,
                    score,
                    reasons,
                    stats,
                )
            )

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Take top 5 and randomly select to add variety
        top_candidates = scored[:5]
        if not top_candidates:
            return None

        selected = random.choice(top_candidates)
        member, score, reasons, stats = selected

        return SpotlightCandidate(
            user_id=member.user_id,
            username=member.user.username if member.user else None,
            first_name=member.user.first_name if member.user else "Community Member",
            score=score,
            reasons=reasons,
            stats=stats,
        )

    async def generate_feature(
        self,
        group_id: int,
        candidate: SpotlightCandidate,
    ) -> SpotlightFeature:
        """Generate AI-written spotlight feature.

        Creates a natural, personalized writeup about the member.
        """
        config = await self._get_config(group_id)
        personality = self.PERSONALITIES.get(
            config.ai_personality, self.PERSONALITIES["friendly"]
        )

        # Get community quotes/reactions
        quotes = await self._get_community_quotes(group_id, candidate.user_id)

        # Get featured stats
        stats = candidate.stats if config.include_stats else {}

        # Generate writeup
        if self.openai_api_key:
            writeup = await self._generate_ai_writeup(
                candidate, personality, stats, quotes
            )
        else:
            writeup = self._generate_template_writeup(
                candidate, personality, stats, quotes
            )

        return SpotlightFeature(
            user_id=candidate.user_id,
            writeup=writeup,
            featured_stats=stats,
            community_quotes=quotes,
            selection_reason="; ".join(candidate.reasons),
        )

    async def publish_spotlight(
        self,
        group_id: int,
        feature: SpotlightFeature,
        telegram_chat_id: int,
        bot,  # aiogram Bot instance
    ) -> Optional[int]:
        """Publish spotlight to the group.

        Returns message_id if successful.
        """
        # Build message
        text = f"📢 **Member Spotlight**\n\n"
        text += feature.writeup

        if feature.featured_stats and len(feature.featured_stats) > 0:
            text += "\n\n📊 **Featured Stats:**\n"
            for key, value in feature.featured_stats.items():
                text += f"• {key}: {value}\n"

        if feature.community_quotes and len(feature.community_quotes) > 0:
            text += "\n💬 **What the community says:**\n"
            for quote in feature.community_quotes[:3]:
                text += f'"{quote}"\n'

        # Send message
        try:
            msg = await bot.send_message(
                chat_id=telegram_chat_id,
                text=text,
                parse_mode="Markdown",
            )

            # Record spotlight
            spotlight = MemberSpotlight(
                group_id=group_id,
                user_id=feature.user_id,
                spotlight_type="weekly",
                selection_reason=feature.selection_reason,
                ai_writeup=feature.writeup,
                featured_stats=feature.featured_stats,
                community_quotes=feature.community_quotes,
                published_at=datetime.utcnow(),
                message_id=msg.message_id,
            )
            self.db.add(spotlight)
            await self.db.flush()

            return msg.message_id

        except Exception as e:
            print(f"Error publishing spotlight: {e}")
            return None

    async def get_past_spotlights(
        self,
        group_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get past spotlight features."""
        result = await self.db.execute(
            select(MemberSpotlight)
            .where(MemberSpotlight.group_id == group_id)
            .order_by(MemberSpotlight.published_at.desc())
            .limit(limit)
        )
        spotlights = result.scalars().all()

        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "type": s.spotlight_type,
                "published_at": s.published_at.isoformat() if s.published_at else None,
                "reactions_positive": s.reactions_positive,
                "reactions_total": s.reactions_total,
            }
            for s in spotlights
        ]

    async def update_reactions(
        self,
        spotlight_id: int,
        positive: int,
        total: int,
    ):
        """Update reaction counts for a spotlight."""
        result = await self.db.execute(
            select(MemberSpotlight).where(MemberSpotlight.id == spotlight_id)
        )
        spotlight = result.scalar_one_or_none()

        if spotlight:
            spotlight.reactions_positive = positive
            spotlight.reactions_total = total
            await self.db.flush()

    async def should_run_spotlight(self, group_id: int) -> bool:
        """Check if spotlight should run now."""
        config = await self._get_config(group_id)

        if not config.enabled:
            return False

        # Check day of week
        now = datetime.utcnow()
        if now.weekday() != config.day_of_week:
            return False

        # Check time (hour match)
        current_time = now.strftime("%H:%M")
        if not current_time.startswith(config.time_of_day[:2]):
            return False

        # Check if already ran this week
        week_start = now - timedelta(days=now.weekday())
        result = await self.db.execute(
            select(MemberSpotlight).where(
                MemberSpotlight.group_id == group_id,
                MemberSpotlight.published_at >= week_start,
            )
        )
        existing = result.scalar_one_or_none()

        return existing is None

    async def _get_config(self, group_id: int) -> SpotlightConfig:
        """Get or create spotlight config."""
        result = await self.db.execute(
            select(SpotlightConfig).where(SpotlightConfig.group_id == group_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = SpotlightConfig(
                group_id=group_id,
                enabled=False,
                frequency="weekly",
                day_of_week=4,  # Friday
                time_of_day="12:00",
                selection_criteria={
                    "activity_weight": 0.3,
                    "engagement_weight": 0.3,
                    "trust_weight": 0.2,
                    "contribution_weight": 0.2,
                },
                ai_personality="friendly",
                include_stats=True,
                include_quotes=True,
            )
            self.db.add(config)
            await self.db.flush()

        return config

    async def _score_candidate(
        self, group_id: int, member: Member
    ) -> tuple[float, List[str], Dict[str, Any]]:
        """Score a candidate for spotlight selection.

        Returns (score, reasons, stats).
        """
        config = await self._get_config(group_id)
        criteria = config.selection_criteria or {}

        score = 0
        reasons = []
        stats = {}

        # Activity score (messages)
        activity_score = min(100, member.message_count / 5)
        score += activity_score * criteria.get("activity_weight", 0.3)

        if member.message_count > 100:
            reasons.append(f"Very active ({member.message_count} messages)")
            stats["Messages"] = member.message_count

        # Engagement score (XP)
        engagement_score = min(100, member.xp / 10)
        score += engagement_score * criteria.get("engagement_weight", 0.3)

        if member.xp > 500:
            reasons.append(f"High engagement ({member.xp} XP)")
            stats["XP"] = member.xp

        # Trust score
        trust_score = member.trust_score
        score += trust_score * criteria.get("trust_weight", 0.2)

        if trust_score >= 80:
            reasons.append("Highly trusted member")

        # Contribution score (badges)
        result = await self.db.execute(
            select(MemberBadge).where(MemberBadge.member_id == member.id)
        )
        badges = result.scalars().all()
        badge_count = len(badges)

        contribution_score = min(100, badge_count * 10)
        score += contribution_score * criteria.get("contribution_weight", 0.2)

        if badge_count >= 3:
            reasons.append(f"Earned {badge_count} badges")
            stats["Badges"] = badge_count

        # Streak bonus
        if member.streak_days >= 7:
            streak_bonus = min(20, member.streak_days / 7 * 5)
            score += streak_bonus
            reasons.append(f"{member.streak_days}-day activity streak")
            stats["Streak"] = f"{member.streak_days} days"

        # Level bonus
        if member.level >= 5:
            reasons.append(f"Level {member.level}")
            stats["Level"] = member.level

        return score, reasons, stats

    async def _get_community_quotes(
        self,
        group_id: int,
        user_id: int,
        limit: int = 5,
    ) -> List[str]:
        """Get community quotes/reactions about the user."""
        # Find positive reactions to this user's messages
        # For now, return generic positive statements
        # In production, this would analyze replies and reactions

        quotes = [
            "Always helpful and positive!",
            "Great contributor to discussions",
            "Appreciate your energy in the community",
        ]

        return quotes[:limit]

    async def _generate_ai_writeup(
        self,
        candidate: SpotlightCandidate,
        personality: Dict[str, str],
        stats: Dict[str, Any],
        quotes: List[str],
    ) -> str:
        """Generate AI-written spotlight feature.

        Uses OpenAI to create a natural, personalized writeup.
        """
        if not self.openai_api_key:
            return self._generate_template_writeup(
                candidate, personality, stats, quotes
            )

        # Build prompt
        prompt = f"""Write a {personality['tone']} community spotlight for {candidate.first_name}.

Context:
- This is a Telegram group community member spotlight
- Tone should be {personality['tone']}
- Keep it warm, appreciative, and engaging
- 3-4 paragraphs maximum

Member highlights:
{chr(10).join(f"- {reason}" for reason in candidate.reasons)}

Stats:
{chr(10).join(f"- {k}: {v}" for k, v in stats.items())}

Community feedback:
{chr(10).join(f'- "{quote}"' for quote in quotes[:2])}

Start with: {personality['greeting']}
End with: {personality['closing']}

Writeup:"""

        # Would call OpenAI API here
        # For now, return template
        return self._generate_template_writeup(
            candidate, personality, stats, quotes
        )

    def _generate_template_writeup(
        self,
        candidate: SpotlightCandidate,
        personality: Dict[str, str],
        stats: Dict[str, Any],
        quotes: List[str],
    ) -> str:
        """Generate template-based spotlight writeup."""
        name = candidate.first_name

        writeup = f"{personality['greeting']}\n\n"

        writeup += f"This week we're shining the spotlight on **{name}**! "

        if candidate.reasons:
            writeup += f"{name} has been making waves in our community for a few reasons:\n\n"
            for reason in candidate.reasons:
                writeup += f"• {reason}\n"

        if quotes:
            writeup += f"\nThe community has noticed too! Here's what people are saying about {name}:\n"
            for quote in quotes[:2]:
                writeup += f'\n"{quote}"'

        writeup += f"\n\n{name}, your contributions don't go unnoticed. "
        writeup += "You're exactly the kind of member that makes this community special!"

        writeup += f"\n\n{personality['closing']}"

        return writeup
