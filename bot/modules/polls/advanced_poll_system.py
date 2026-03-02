"""
Advanced Poll System for Nexus

Extends Telegram's native polls with:
- Timed closing with callbacks
- Vote-based moderation actions
- Recurring polls
- Poll history and analytics
- Weighted voting by role/reputation
- Conditional polls (show results only after voting)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from aiogram.types import Message, Poll as TelegramPoll, CallbackQuery
from pydantic import BaseModel, Field

from bot.core.context import NexusContext
from shared.redis_client import GroupScopedRedis


class PollStatus(str, Enum):
    """Poll lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class PollType(str, Enum):
    """Extended poll types."""
    SINGLE = "single"  # Single choice
    MULTIPLE = "multiple"  # Multiple choice
    QUIZ = "quiz"  # Quiz with correct answer
    RANKED = "ranked"  # Ranked choice (IRV)
    WEIGHTED = "weighted"  # Weighted by user role/reputation
    CONDITIONAL = "conditional"  # Results hidden until vote
    APPROVAL = "approval"  # Approval voting


class VoteAction(str, Enum):
    """Actions triggered by vote thresholds."""
    NONE = "none"
    PIN = "pin"  # Pin message at threshold
    ANNOUNCE = "announce"  # Announce in channel
    RESTRICT = "restrict"  # Restrict user (if user poll)
    MUTE = "mute"  # Mute user
    KICK = "kick"  # Kick user
    BAN = "ban"  # Ban user
    ROLE_GRANT = "role_grant"  # Grant role
    TRIGGER_FLOW = "trigger_flow"  # Trigger automation flow


class PollVisibility(str, Enum):
    """When poll results are visible."""
    ALWAYS = "always"
    AFTER_VOTE = "after_vote"
    AFTER_CLOSE = "after_close"
    NEVER = "never"  # Anonymous forever


@dataclass
class PollOption:
    """Extended poll option."""
    id: str
    text: str
    index: int
    is_correct: bool = False  # For quizzes
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Vote tracking
    voter_ids: Set[int] = field(default_factory=set)
    voter_weights: Dict[int, float] = field(default_factory=dict)
    
    @property
    def vote_count(self) -> int:
        return len(self.voter_ids)
    
    @property
    def weighted_count(self) -> float:
        return sum(self.voter_weights.values())


@dataclass
class PollVoteAction:
    """Action triggered by vote conditions."""
    action_type: VoteAction
    threshold_type: str = "percentage"  # percentage, count, majority
    threshold_value: float = 0.5
    target_user_id: Optional[int] = None
    target_role: Optional[str] = None
    custom_message: Optional[str] = None
    triggered_at: Optional[datetime] = None
    executed: bool = False


@dataclass
class PollAnalytics:
    """Analytics for a poll."""
    total_votes: int = 0
    unique_voters: int = 0
    votes_by_hour: Dict[int, int] = field(default_factory=dict)
    votes_by_role: Dict[str, int] = field(default_factory=dict)
    changed_votes: int = 0  # Users who changed their vote
    average_decision_time_seconds: float = 0.0
    participation_rate: float = 0.0
    
    def record_vote(self, hour: int, role: str, decision_time: Optional[float] = None):
        """Record a vote for analytics."""
        self.total_votes += 1
        self.votes_by_hour[hour] = self.votes_by_hour.get(hour, 0) + 1
        self.votes_by_role[role] = self.votes_by_role.get(role, 0) + 1
        
        if decision_time:
            # Update rolling average
            self.average_decision_time_seconds = (
                (self.average_decision_time_seconds * (self.total_votes - 1) + decision_time)
                / self.total_votes
            )


@dataclass
class AdvancedPoll:
    """
    Extended poll with advanced features.
    
    This is stored in Redis for active polls and synced to DB for history.
    """
    # Identity
    poll_id: str
    group_id: int
    created_by: int
    message_id: Optional[int] = None
    chat_id: Optional[int] = None
    
    # Content
    question: str = ""
    description: Optional[str] = None
    options: List[PollOption] = field(default_factory=list)
    poll_type: PollType = PollType.SINGLE
    
    # Configuration
    is_anonymous: bool = True
    allows_multiple: bool = False
    max_choices: int = 1
    visibility: PollVisibility = PollVisibility.ALWAYS
    allow_change_vote: bool = True
    weight_by_role: bool = False
    weight_by_reputation: bool = False
    
    # Scheduling
    status: PollStatus = PollStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Recurring
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # cron expression
    recurrence_count: int = 0
    max_recurrences: Optional[int] = None
    parent_poll_id: Optional[str] = None  # For recurring instances
    
    # Vote actions
    vote_actions: List[PollVoteAction] = field(default_factory=list)
    
    # Analytics
    analytics: PollAnalytics = field(default_factory=PollAnalytics)
    voter_first_seen: Dict[int, datetime] = field(default_factory=dict)
    
    # Results
    final_results: Optional[Dict[str, Any]] = None
    winning_option_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "poll_id": self.poll_id,
            "group_id": self.group_id,
            "created_by": self.created_by,
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "question": self.question,
            "description": self.description,
            "options": [
                {
                    "id": opt.id,
                    "text": opt.text,
                    "index": opt.index,
                    "is_correct": opt.is_correct,
                    "metadata": opt.metadata,
                    "voter_ids": list(opt.voter_ids),
                    "voter_weights": opt.voter_weights,
                }
                for opt in self.options
            ],
            "poll_type": self.poll_type.value,
            "is_anonymous": self.is_anonymous,
            "allows_multiple": self.allows_multiple,
            "max_choices": self.max_choices,
            "visibility": self.visibility.value,
            "allow_change_vote": self.allow_change_vote,
            "weight_by_role": self.weight_by_role,
            "weight_by_reputation": self.weight_by_reputation,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "opens_at": self.opens_at.isoformat() if self.opens_at else None,
            "closes_at": self.closes_at.isoformat() if self.closes_at else None,
            "timezone": self.timezone,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "recurrence_count": self.recurrence_count,
            "max_recurrences": self.max_recurrences,
            "parent_poll_id": self.parent_poll_id,
            "vote_actions": [
                {
                    "action_type": va.action_type.value,
                    "threshold_type": va.threshold_type,
                    "threshold_value": va.threshold_value,
                    "target_user_id": va.target_user_id,
                    "target_role": va.target_role,
                    "custom_message": va.custom_message,
                    "triggered_at": va.triggered_at.isoformat() if va.triggered_at else None,
                    "executed": va.executed,
                }
                for va in self.vote_actions
            ],
            "analytics": {
                "total_votes": self.analytics.total_votes,
                "unique_voters": self.analytics.unique_voters,
                "votes_by_hour": self.analytics.votes_by_hour,
                "votes_by_role": self.analytics.votes_by_role,
                "changed_votes": self.analytics.changed_votes,
                "average_decision_time_seconds": self.analytics.average_decision_time_seconds,
                "participation_rate": self.analytics.participation_rate,
            },
            "voter_first_seen": {
                str(k): v.isoformat() for k, v in self.voter_first_seen.items()
            },
            "final_results": self.final_results,
            "winning_option_id": self.winning_option_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdvancedPoll":
        """Create from dictionary."""
        poll = cls(
            poll_id=data["poll_id"],
            group_id=data["group_id"],
            created_by=data["created_by"],
            message_id=data.get("message_id"),
            chat_id=data.get("chat_id"),
            question=data.get("question", ""),
            description=data.get("description"),
            options=[
                PollOption(
                    id=opt["id"],
                    text=opt["text"],
                    index=opt["index"],
                    is_correct=opt.get("is_correct", False),
                    metadata=opt.get("metadata", {}),
                    voter_ids=set(opt.get("voter_ids", [])),
                    voter_weights=opt.get("voter_weights", {}),
                )
                for opt in data.get("options", [])
            ],
            poll_type=PollType(data.get("poll_type", "single")),
            is_anonymous=data.get("is_anonymous", True),
            allows_multiple=data.get("allows_multiple", False),
            max_choices=data.get("max_choices", 1),
            visibility=PollVisibility(data.get("visibility", "always")),
            allow_change_vote=data.get("allow_change_vote", True),
            weight_by_role=data.get("weight_by_role", False),
            weight_by_reputation=data.get("weight_by_reputation", False),
            status=PollStatus(data.get("status", "draft")),
            created_at=datetime.fromisoformat(data["created_at"]),
            opens_at=datetime.fromisoformat(data["opens_at"]) if data.get("opens_at") else None,
            closes_at=datetime.fromisoformat(data["closes_at"]) if data.get("closes_at") else None,
            timezone=data.get("timezone", "UTC"),
            is_recurring=data.get("is_recurring", False),
            recurrence_pattern=data.get("recurrence_pattern"),
            recurrence_count=data.get("recurrence_count", 0),
            max_recurrences=data.get("max_recurrences"),
            parent_poll_id=data.get("parent_poll_id"),
            vote_actions=[
                PollVoteAction(
                    action_type=VoteAction(va["action_type"]),
                    threshold_type=va.get("threshold_type", "percentage"),
                    threshold_value=va.get("threshold_value", 0.5),
                    target_user_id=va.get("target_user_id"),
                    target_role=va.get("target_role"),
                    custom_message=va.get("custom_message"),
                    triggered_at=datetime.fromisoformat(va["triggered_at"]) if va.get("triggered_at") else None,
                    executed=va.get("executed", False),
                )
                for va in data.get("vote_actions", [])
            ],
            voter_first_seen={
                int(k): datetime.fromisoformat(v)
                for k, v in data.get("voter_first_seen", {}).items()
            },
            final_results=data.get("final_results"),
            winning_option_id=data.get("winning_option_id"),
        )
        
        # Restore analytics
        analytics_data = data.get("analytics", {})
        poll.analytics = PollAnalytics(
            total_votes=analytics_data.get("total_votes", 0),
            unique_voters=analytics_data.get("unique_voters", 0),
            votes_by_hour=analytics_data.get("votes_by_hour", {}),
            votes_by_role=analytics_data.get("votes_by_role", {}),
            changed_votes=analytics_data.get("changed_votes", 0),
            average_decision_time_seconds=analytics_data.get("average_decision_time_seconds", 0.0),
            participation_rate=analytics_data.get("participation_rate", 0.0),
        )
        
        return poll
    
    def calculate_weights(self, user_id: int, role: str, reputation: int) -> float:
        """Calculate voting weight for a user."""
        weight = 1.0
        
        if self.weight_by_role:
            role_weights = {
                "owner": 5.0,
                "admin": 3.0,
                "moderator": 2.0,
                "trusted": 1.5,
                "member": 1.0,
                "new": 0.5,
            }
            weight *= role_weights.get(role, 1.0)
        
        if self.weight_by_reputation:
            # Reputation 0-100, scale to 0.5-2.0
            rep_weight = 0.5 + (reputation / 100) * 1.5
            weight *= rep_weight
        
        return weight
    
    def get_results(self) -> Dict[str, Any]:
        """Get current poll results."""
        total_votes = sum(opt.vote_count for opt in self.options)
        total_weighted = sum(opt.weighted_count for opt in self.options)
        
        results = {
            "poll_id": self.poll_id,
            "total_votes": total_votes,
            "total_weighted": total_weighted,
            "status": self.status.value,
            "is_anonymous": self.is_anonymous,
            "options": [],
        }
        
        for opt in self.options:
            percentage = (opt.vote_count / total_votes * 100) if total_votes > 0 else 0
            weighted_pct = (opt.weighted_count / total_weighted * 100) if total_weighted > 0 else 0
            
            results["options"].append({
                "id": opt.id,
                "text": opt.text,
                "votes": opt.vote_count,
                "weighted_votes": opt.weighted_count,
                "percentage": round(percentage, 1),
                "weighted_percentage": round(weighted_pct, 1),
                "is_correct": opt.is_correct if self.poll_type == PollType.QUIZ else None,
            })
        
        # Sort by votes
        results["options"].sort(key=lambda x: x["votes"], reverse=True)
        
        return results
    
    def check_vote_actions(self) -> List[PollVoteAction]:
        """Check if any vote action thresholds have been met."""
        results = self.get_results()
        total_votes = results["total_votes"]
        
        triggered = []
        for action in self.vote_actions:
            if action.executed:
                continue
            
            # Find leading option
            leading = max(results["options"], key=lambda x: x["votes"]) if results["options"] else None
            if not leading:
                continue
            
            threshold_met = False
            if action.threshold_type == "percentage":
                threshold_met = leading["percentage"] >= action.threshold_value * 100
            elif action.threshold_type == "count":
                threshold_met = leading["votes"] >= action.threshold_value
            elif action.threshold_type == "majority":
                threshold_met = leading["percentage"] > 50
            
            if threshold_met:
                action.triggered_at = datetime.utcnow()
                triggered.append(action)
        
        return triggered


class AdvancedPollManager:
    """Manages advanced polls using Redis for active state."""
    
    def __init__(self, redis: GroupScopedRedis):
        self.redis = redis
        self._handlers: Dict[VoteAction, Callable] = {}
    
    def _poll_key(self, poll_id: str) -> str:
        return f"poll:{poll_id}"
    
    def _group_polls_key(self) -> str:
        return "polls:active"
    
    def _scheduled_key(self) -> str:
        return "polls:scheduled"
    
    def _recurring_key(self) -> str:
        return "polls:recurring"
    
    async def create_poll(
        self,
        group_id: int,
        created_by: int,
        question: str,
        options: List[str],
        poll_type: PollType = PollType.SINGLE,
        **kwargs
    ) -> AdvancedPoll:
        """Create a new advanced poll."""
        poll_id = f"poll_{group_id}_{uuid4().hex[:12]}"
        
        poll_options = [
            PollOption(
                id=f"opt_{i}_{uuid4().hex[:6]}",
                text=text,
                index=i,
            )
            for i, text in enumerate(options)
        ]
        
        poll = AdvancedPoll(
            poll_id=poll_id,
            group_id=group_id,
            created_by=created_by,
            question=question,
            options=poll_options,
            poll_type=poll_type,
            **kwargs
        )
        
        await self._save_poll(poll)
        await self.redis.sadd(self._group_polls_key(), poll_id)
        
        if poll.status == PollStatus.SCHEDULED and poll.opens_at:
            # Schedule for future
            await self.redis.zadd(
                self._scheduled_key(),
                {poll_id: poll.opens_at.timestamp()}
            )
        
        if poll.is_recurring:
            await self.redis.sadd(self._recurring_key(), poll_id)
        
        return poll
    
    async def get_poll(self, poll_id: str) -> Optional[AdvancedPoll]:
        """Get a poll by ID."""
        data = await self.redis.get_json(self._poll_key(poll_id))
        if not data:
            return None
        return AdvancedPoll.from_dict(data)
    
    async def update_poll(self, poll: AdvancedPoll) -> bool:
        """Update a poll."""
        await self._save_poll(poll)
        return True
    
    async def delete_poll(self, poll_id: str) -> bool:
        """Delete a poll."""
        await self.redis.delete(self._poll_key(poll_id))
        await self.redis.srem(self._group_polls_key(), poll_id)
        await self.redis.srem(self._recurring_key(), poll_id)
        await self.redis.zrem(self._scheduled_key(), poll_id)
        return True
    
    async def record_vote(
        self,
        poll_id: str,
        user_id: int,
        option_ids: List[str],
        user_role: str = "member",
        reputation: int = 50,
    ) -> Tuple[bool, str]:
        """
        Record a vote.
        
        Returns:
            (success, message)
        """
        poll = await self.get_poll(poll_id)
        if not poll:
            return False, "Poll not found"
        
        if poll.status != PollStatus.ACTIVE:
            return False, "Poll is not active"
        
        if poll.closes_at and datetime.utcnow() > poll.closes_at:
            poll.status = PollStatus.CLOSED
            await self._save_poll(poll)
            return False, "Poll has closed"
        
        # Check if user already voted
        previous_vote = None
        for opt in poll.options:
            if user_id in opt.voter_ids:
                if not poll.allow_change_vote:
                    return False, "You have already voted"
                previous_vote = opt
                break
        
        # Remove previous vote if changing
        if previous_vote:
            previous_vote.voter_ids.discard(user_id)
            previous_vote.voter_weights.pop(user_id, None)
            poll.analytics.changed_votes += 1
        
        # Validate option count
        if len(option_ids) > poll.max_choices:
            return False, f"You can select up to {poll.max_choices} options"
        
        # Calculate weight
        weight = poll.calculate_weights(user_id, user_role, reputation)
        
        # Record votes
        first_seen = user_id not in poll.voter_first_seen
        if first_seen:
            poll.voter_first_seen[user_id] = datetime.utcnow()
            poll.analytics.unique_voters += 1
        
        # Calculate decision time
        decision_time = None
        if not first_seen:
            decision_time = (datetime.utcnow() - poll.voter_first_seen[user_id]).total_seconds()
        
        for opt_id in option_ids:
            opt = next((o for o in poll.options if o.id == opt_id), None)
            if opt:
                opt.voter_ids.add(user_id)
                opt.voter_weights[user_id] = weight
        
        # Update analytics
        current_hour = datetime.utcnow().hour
        poll.analytics.record_vote(current_hour, user_role, decision_time)
        
        await self._save_poll(poll)
        
        # Check for vote action triggers
        triggered = poll.check_vote_actions()
        for action in triggered:
            await self._execute_vote_action(poll, action)
        
        return True, "Vote recorded"
    
    async def close_poll(self, poll_id: str, manual: bool = False) -> Optional[AdvancedPoll]:
        """Close a poll and calculate final results."""
        poll = await self.get_poll(poll_id)
        if not poll:
            return None
        
        poll.status = PollStatus.CLOSED
        
        # Calculate results
        results = poll.get_results()
        poll.final_results = results
        
        # Determine winner
        if results["options"]:
            winner = max(results["options"], key=lambda x: x["votes"])
            winning_opt = next((o for o in poll.options if o.id == winner["id"]), None)
            if winning_opt:
                poll.winning_option_id = winning_opt.id
        
        await self._save_poll(poll)
        await self.redis.srem(self._group_polls_key(), poll_id)
        
        # Persist to database
        await self._persist_to_database(poll)
        
        return poll
    
    async def get_active_polls(self) -> List[AdvancedPoll]:
        """Get all active polls."""
        poll_ids = await self.redis.smembers(self._group_polls_key())
        polls = []
        
        for poll_id in poll_ids:
            poll = await self.get_poll(poll_id)
            if poll and poll.status == PollStatus.ACTIVE:
                polls.append(poll)
        
        return polls
    
    async def get_scheduled_polls(self, before: datetime) -> List[AdvancedPoll]:
        """Get polls scheduled to open before a time."""
        poll_ids = await self.redis.zrangebyscore(
            self._scheduled_key(),
            0,
            before.timestamp()
        )
        
        polls = []
        for poll_id in poll_ids:
            poll = await self.get_poll(poll_id)
            if poll:
                polls.append(poll)
        
        return polls
    
    async def get_polls_for_closing(self, before: datetime) -> List[AdvancedPoll]:
        """Get polls that should be closed."""
        all_active = await self.get_active_polls()
        to_close = []
        
        for poll in all_active:
            if poll.closes_at and poll.closes_at <= before:
                to_close.append(poll)
        
        return to_close
    
    async def create_recurring_instance(self, parent_poll_id: str) -> Optional[AdvancedPoll]:
        """Create a new instance of a recurring poll."""
        parent = await self.get_poll(parent_poll_id)
        if not parent:
            return None
        
        # Check max recurrences
        if parent.max_recurrences and parent.recurrence_count >= parent.max_recurrences:
            return None
        
        # Create new instance
        instance = await self.create_poll(
            group_id=parent.group_id,
            created_by=parent.created_by,
            question=parent.question,
            options=[opt.text for opt in parent.options],
            poll_type=parent.poll_type,
            is_anonymous=parent.is_anonymous,
            allows_multiple=parent.allows_multiple,
            max_choices=parent.max_choices,
            visibility=parent.visibility,
            allow_change_vote=parent.allow_change_vote,
            weight_by_role=parent.weight_by_role,
            weight_by_reputation=parent.weight_by_reputation,
            parent_poll_id=parent_poll_id,
        )
        
        # Update parent
        parent.recurrence_count += 1
        await self._save_poll(parent)
        
        return instance
    
    def register_vote_action_handler(
        self,
        action_type: VoteAction,
        handler: Callable[[AdvancedPoll, PollVoteAction], Coroutine]
    ):
        """Register a handler for vote actions."""
        self._handlers[action_type] = handler
    
    async def _execute_vote_action(self, poll: AdvancedPoll, action: PollVoteAction):
        """Execute a vote action."""
        handler = self._handlers.get(action.action_type)
        if handler:
            try:
                await handler(poll, action)
                action.executed = True
                await self._save_poll(poll)
            except Exception as e:
                print(f"Error executing vote action: {e}")
    
    async def _save_poll(self, poll: AdvancedPoll):
        """Save poll to Redis."""
        key = self._poll_key(poll.poll_id)
        # Set TTL based on poll status
        if poll.status == PollStatus.ACTIVE:
            ttl = 86400 * 7  # 7 days for active polls
        else:
            ttl = 86400  # 1 day for closed polls
        await self.redis.set_json(key, poll.to_dict(), expire=ttl)
    
    async def _persist_to_database(self, poll: AdvancedPoll):
        """Persist closed poll to database."""
        # This would be called to save to PostgreSQL
        # Implementation depends on your DB layer
        pass


class PollScheduler:
    """
    Scheduler for poll lifecycle events.
    
    Handles:
    - Opening scheduled polls
    - Closing expired polls
    - Creating recurring poll instances
    """
    
    def __init__(self, poll_manager: AdvancedPollManager):
        self.poll_manager = poll_manager
    
    async def process_scheduled_polls(self):
        """Process polls scheduled to open."""
        now = datetime.utcnow()
        scheduled = await self.poll_manager.get_scheduled_polls(now)
        
        for poll in scheduled:
            poll.status = PollStatus.ACTIVE
            await self.poll_manager.update_poll(poll)
            await self.poll_manager.redis.zrem(
                self.poll_manager._scheduled_key(),
                poll.poll_id
            )
            # Here you would actually send the poll message
            print(f"Poll {poll.poll_id} is now active")
    
    async def process_closing_polls(self):
        """Process polls that need to be closed."""
        now = datetime.utcnow()
        to_close = await self.poll_manager.get_polls_for_closing(now)
        
        for poll in to_close:
            await self.poll_manager.close_poll(poll.poll_id)
            print(f"Poll {poll.poll_id} has been closed")
    
    async def process_recurring_polls(self):
        """Create new instances of recurring polls."""
        # This would check based on recurrence pattern
        pass


class PollAnalyticsEngine:
    """
    Analytics engine for poll data.
    
    Provides:
    - Participation trends
    - Vote pattern analysis
    - Demographic breakdowns
    - Comparative analysis across polls
    """
    
    def __init__(self, redis: GroupScopedRedis):
        self.redis = redis
    
    async def generate_report(self, poll_id: str) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        # This would aggregate data from Redis and DB
        return {
            "poll_id": poll_id,
            "generated_at": datetime.utcnow().isoformat(),
            "report": "Analytics placeholder",
        }
    
    async def get_group_analytics(self, group_id: int, days: int = 30) -> Dict[str, Any]:
        """Get analytics for all polls in a group over time."""
        return {
            "group_id": group_id,
            "period_days": days,
            "report": "Group analytics placeholder",
        }
