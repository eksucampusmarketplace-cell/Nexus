"""Shared Group Challenges Service for Nexus.

Manages collective group-wide goals that the entire community works
toward together to unlock rewards.

Features:
- Multiple challenge types (messages, members, engagement, activity)
- Progress tracking for all participants
- Tiered rewards based on contribution level
- Cross-module intelligence integration for personalized challenges
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    ChallengeProgress,
    Group,
    GroupChallenge,
    Member,
)


@dataclass
class ChallengeStats:
    """Challenge statistics."""
    challenge_id: int
    total_participants: int
    total_contribution: int
    percent_complete: float
    top_contributors: List[Dict[str, Any]]
    projected_completion: Optional[datetime]


@dataclass
class UserChallengeStatus:
    """User's status in a challenge."""
    challenge_id: int
    user_id: int
    contribution: int
    percent_complete: float
    rank: int
    reward_claimed: bool
    next_milestone: Optional[int]


class ChallengeService:
    """Group challenges management service."""

    # Challenge types and their metrics
    CHALLENGE_TYPES = {
        "messages": {
            "name": "Message Marathon",
            "description": "Send messages to reach the goal",
            "metric": "message_count",
        },
        "active_members": {
            "name": "Active Army",
            "description": "Get active members participating",
            "metric": "unique_active_users",
        },
        "engagement": {
            "name": "Engagement Explosion",
            "description": "Boost overall engagement",
            "metric": "total_engagement_score",
        },
        "reactions": {
            "name": "Reaction Rally",
            "description": "Share reactions and positivity",
            "metric": "reaction_count",
        },
        "streak": {
            "name": "Streak Stars",
            "description": "Maintain activity streaks",
            "metric": "total_streak_days",
        },
        "welcome": {
            "name": "Welcome Wagon",
            "description": "Welcome new members",
            "metric": "welcomes_count",
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_challenge(
        self,
        group_id: int,
        title: str,
        description: str,
        challenge_type: str,
        target_value: int,
        duration_days: int,
        reward_type: str,
        reward_config: Dict[str, Any],
        created_by: int,
    ) -> GroupChallenge:
        """Create a new group challenge."""
        now = datetime.utcnow()

        challenge = GroupChallenge(
            group_id=group_id,
            title=title,
            description=description,
            challenge_type=challenge_type,
            target_value=target_value,
            current_value=0,
            target_metric=self.CHALLENGE_TYPES[challenge_type]["metric"],
            start_date=now,
            end_date=now + timedelta(days=duration_days),
            reward_type=reward_type,
            reward_config=reward_config,
            status="active",
            created_by=created_by,
            created_at=now,
        )

        self.db.add(challenge)
        await self.db.flush()

        return challenge

    async def record_contribution(
        self,
        challenge_id: int,
        user_id: int,
        amount: int = 1,
    ) -> UserChallengeStatus:
        """Record a user's contribution to a challenge."""
        # Get challenge
        result = await self.db.execute(
            select(GroupChallenge).where(
                GroupChallenge.id == challenge_id,
                GroupChallenge.status == "active",
            )
        )
        challenge = result.scalar_one_or_none()

        if not challenge:
            raise ValueError("Challenge not found or not active")

        # Get or create progress record
        result = await self.db.execute(
            select(ChallengeProgress).where(
                ChallengeProgress.challenge_id == challenge_id,
                ChallengeProgress.user_id == user_id,
            )
        )
        progress = result.scalar_one_or_none()

        if progress:
            progress.contribution += amount
            progress.updated_at = datetime.utcnow()
        else:
            progress = ChallengeProgress(
                challenge_id=challenge_id,
                user_id=user_id,
                contribution=amount,
                percent_complete=0.0,
                reward_claimed=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(progress)

        # Calculate percentage
        if challenge.target_value > 0:
            progress.percent_complete = min(
                100, (progress.contribution / challenge.target_value) * 100
            )

        await self.db.flush()

        # Update challenge total
        await self._update_challenge_total(challenge_id)

        # Get rank
        rank = await self._get_user_rank(challenge_id, user_id)
        progress.rank = rank

        await self.db.flush()

        # Check if challenge completed
        await self._check_completion(challenge)

        return UserChallengeStatus(
            challenge_id=challenge_id,
            user_id=user_id,
            contribution=progress.contribution,
            percent_complete=progress.percent_complete,
            rank=rank,
            reward_claimed=progress.reward_claimed,
            next_milestone=self._get_next_milestone(progress.contribution),
        )

    async def get_active_challenges(
        self,
        group_id: int,
    ) -> List[Dict[str, Any]]:
        """Get all active challenges for a group."""
        now = datetime.utcnow()

        result = await self.db.execute(
            select(GroupChallenge).where(
                GroupChallenge.group_id == group_id,
                GroupChallenge.status == "active",
                GroupChallenge.end_date > now,
            )
        )
        challenges = result.scalars().all()

        challenge_list = []
        for challenge in challenges:
            stats = await self._get_challenge_stats(challenge.id)

            challenge_list.append(
                {
                    "id": challenge.id,
                    "title": challenge.title,
                    "description": challenge.description,
                    "type": challenge.challenge_type,
                    "target_value": challenge.target_value,
                    "current_value": challenge.current_value,
                    "percent_complete": (
                        (challenge.current_value / challenge.target_value) * 100
                        if challenge.target_value > 0
                        else 0
                    ),
                    "end_date": challenge.end_date.isoformat(),
                    "time_remaining": self._format_time_remaining(
                        challenge.end_date
                    ),
                    "participant_count": stats.total_participants,
                    "reward_type": challenge.reward_type,
                }
            )

        return challenge_list

    async def get_challenge_details(
        self,
        challenge_id: int,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get detailed challenge information."""
        result = await self.db.execute(
            select(GroupChallenge).where(GroupChallenge.id == challenge_id)
        )
        challenge = result.scalar_one_or_none()

        if not challenge:
            raise ValueError("Challenge not found")

        stats = await self._get_challenge_stats(challenge_id)

        details = {
            "id": challenge.id,
            "title": challenge.title,
            "description": challenge.description,
            "type": challenge.challenge_type,
            "target_value": challenge.target_value,
            "current_value": challenge.current_value,
            "percent_complete": (
                (challenge.current_value / challenge.target_value) * 100
                if challenge.target_value > 0
                else 0
            ),
            "start_date": challenge.start_date.isoformat(),
            "end_date": challenge.end_date.isoformat(),
            "status": challenge.status,
            "reward_type": challenge.reward_type,
            "reward_config": challenge.reward_config,
            "stats": {
                "total_participants": stats.total_participants,
                "projected_completion": (
                    stats.projected_completion.isoformat()
                    if stats.projected_completion
                    else None
                ),
            },
            "leaderboard": stats.top_contributors,
        }

        if user_id:
            user_status = await self._get_user_challenge_status(
                challenge_id, user_id
            )
            details["user_status"] = {
                "contribution": user_status.contribution,
                "percent_complete": user_status.percent_complete,
                "rank": user_status.rank,
                "reward_claimed": user_status.reward_claimed,
            }

        return details

    async def claim_reward(
        self,
        challenge_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """Claim reward for challenge participation."""
        result = await self.db.execute(
            select(ChallengeProgress).where(
                ChallengeProgress.challenge_id == challenge_id,
                ChallengeProgress.user_id == user_id,
            )
        )
        progress = result.scalar_one_or_none()

        if not progress:
            raise ValueError("No participation record found")

        if progress.reward_claimed:
            raise ValueError("Reward already claimed")

        # Get challenge
        result = await self.db.execute(
            select(GroupChallenge).where(GroupChallenge.id == challenge_id)
        )
        challenge = result.scalar_one_or_none()

        if not challenge or challenge.status != "completed":
            raise ValueError("Challenge not completed yet")

        # Calculate reward tier based on contribution
        contribution_ratio = progress.contribution / challenge.target_value

        if contribution_ratio >= 0.5:
            tier = "gold"
        elif contribution_ratio >= 0.25:
            tier = "silver"
        elif contribution_ratio >= 0.1:
            tier = "bronze"
        else:
            tier = "participant"

        # Get reward for tier
        reward_config = challenge.reward_config or {}
        tier_rewards = reward_config.get("tiers", {})
        reward = tier_rewards.get(tier, {"type": "xp", "amount": 50})

        # Mark as claimed
        progress.reward_claimed = True
        progress.claimed_at = datetime.utcnow()
        await self.db.flush()

        return {
            "tier": tier,
            "reward": reward,
            "contribution": progress.contribution,
            "rank": progress.rank,
        }

    async def end_challenge(
        self,
        challenge_id: int,
        cancelled: bool = False,
    ):
        """End a challenge."""
        result = await self.db.execute(
            select(GroupChallenge).where(GroupChallenge.id == challenge_id)
        )
        challenge = result.scalar_one_or_none()

        if not challenge:
            raise ValueError("Challenge not found")

        if cancelled:
            challenge.status = "cancelled"
        else:
            challenge.status = "completed"
            challenge.completed_at = datetime.utcnow()

        await self.db.flush()

    async def get_user_challenges(
        self,
        group_id: int,
        user_id: int,
    ) -> List[Dict[str, Any]]:
        """Get all challenges a user is participating in."""
        # Get active challenges in group
        result = await self.db.execute(
            select(GroupChallenge).where(
                GroupChallenge.group_id == group_id,
                GroupChallenge.status == "active",
            )
        )
        challenges = result.scalars().all()

        user_challenges = []
        for challenge in challenges:
            # Get user's progress
            result = await self.db.execute(
                select(ChallengeProgress).where(
                    ChallengeProgress.challenge_id == challenge.id,
                    ChallengeProgress.user_id == user_id,
                )
            )
            progress = result.scalar_one_or_none()

            if progress:
                user_challenges.append(
                    {
                        "challenge_id": challenge.id,
                        "title": challenge.title,
                        "contribution": progress.contribution,
                        "percent_complete": progress.percent_complete,
                        "rank": progress.rank,
                        "target_value": challenge.target_value,
                        "end_date": challenge.end_date.isoformat(),
                    }
                )

        return user_challenges

    async def _get_challenge_stats(self, challenge_id: int) -> ChallengeStats:
        """Get statistics for a challenge."""
        # Total participants
        result = await self.db.execute(
            select(func.count(ChallengeProgress.id)).where(
                ChallengeProgress.challenge_id == challenge_id
            )
        )
        participant_count = result.scalar() or 0

        # Total contribution
        result = await self.db.execute(
            select(func.sum(ChallengeProgress.contribution)).where(
                ChallengeProgress.challenge_id == challenge_id
            )
        )
        total_contribution = result.scalar() or 0

        # Top contributors
        result = await self.db.execute(
            select(
                ChallengeProgress.user_id,
                ChallengeProgress.contribution,
            )
            .where(ChallengeProgress.challenge_id == challenge_id)
            .order_by(ChallengeProgress.contribution.desc())
            .limit(10)
        )
        top = result.all()

        top_contributors = []
        for rank, (uid, contribution) in enumerate(top, 1):
            top_contributors.append(
                {
                    "rank": rank,
                    "user_id": uid,
                    "contribution": contribution,
                }
            )

        # Get challenge for percentage
        result = await self.db.execute(
            select(GroupChallenge).where(GroupChallenge.id == challenge_id)
        )
        challenge = result.scalar_one()

        percent_complete = (
            (challenge.current_value / challenge.target_value) * 100
            if challenge.target_value > 0
            else 0
        )

        # Project completion
        projected_completion = None
        if percent_complete > 0 and percent_complete < 100:
            elapsed = (datetime.utcnow() - challenge.start_date).total_seconds()
            if elapsed > 0:
                rate = challenge.current_value / elapsed
                remaining = challenge.target_value - challenge.current_value
                seconds_remaining = remaining / rate
                projected_completion = datetime.utcnow() + timedelta(
                    seconds=seconds_remaining
                )

        return ChallengeStats(
            challenge_id=challenge_id,
            total_participants=participant_count,
            total_contribution=total_contribution,
            percent_complete=percent_complete,
            top_contributors=top_contributors,
            projected_completion=projected_completion,
        )

    async def _get_user_challenge_status(
        self,
        challenge_id: int,
        user_id: int,
    ) -> UserChallengeStatus:
        """Get user's status in a challenge."""
        result = await self.db.execute(
            select(ChallengeProgress).where(
                ChallengeProgress.challenge_id == challenge_id,
                ChallengeProgress.user_id == user_id,
            )
        )
        progress = result.scalar_one_or_none()

        if not progress:
            return UserChallengeStatus(
                challenge_id=challenge_id,
                user_id=user_id,
                contribution=0,
                percent_complete=0.0,
                rank=0,
                reward_claimed=False,
                next_milestone=100,
            )

        rank = await self._get_user_rank(challenge_id, user_id)

        return UserChallengeStatus(
            challenge_id=challenge_id,
            user_id=user_id,
            contribution=progress.contribution,
            percent_complete=progress.percent_complete,
            rank=rank,
            reward_claimed=progress.reward_claimed,
            next_milestone=self._get_next_milestone(progress.contribution),
        )

    async def _update_challenge_total(self, challenge_id: int):
        """Update challenge's current total."""
        result = await self.db.execute(
            select(func.sum(ChallengeProgress.contribution)).where(
                ChallengeProgress.challenge_id == challenge_id
            )
        )
        total = result.scalar() or 0

        result = await self.db.execute(
            select(GroupChallenge).where(GroupChallenge.id == challenge_id)
        )
        challenge = result.scalar_one()

        challenge.current_value = total
        await self.db.flush()

    async def _get_user_rank(self, challenge_id: int, user_id: int) -> int:
        """Get user's rank in challenge."""
        result = await self.db.execute(
            select(ChallengeProgress.user_id)
            .where(ChallengeProgress.challenge_id == challenge_id)
            .order_by(ChallengeProgress.contribution.desc())
        )
        users = result.scalars().all()

        try:
            return users.index(user_id) + 1
        except ValueError:
            return 0

    async def _check_completion(self, challenge: GroupChallenge):
        """Check if challenge is complete."""
        if challenge.current_value >= challenge.target_value:
            if challenge.status == "active":
                challenge.status = "completed"
                challenge.completed_at = datetime.utcnow()
                await self.db.flush()

    def _get_next_milestone(self, contribution: int) -> int:
        """Get next milestone for a contribution amount."""
        milestones = [10, 25, 50, 100, 250, 500, 1000]
        for m in milestones:
            if contribution < m:
                return m
        return milestones[-1] * 2

    def _format_time_remaining(self, end_date: datetime) -> str:
        """Format time remaining until end date."""
        remaining = end_date - datetime.utcnow()

        if remaining.total_seconds() <= 0:
            return "Ended"

        days = remaining.days
        hours = remaining.seconds // 3600

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            minutes = (remaining.seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            minutes = remaining.seconds // 60
            return f"{minutes}m"
