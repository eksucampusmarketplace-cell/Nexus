"""
Event Bus - Central event broadcasting system for Nexus.

This module implements a Redis pub/sub based event bus that enables
real-time synchronization across all services (bot, API, worker).

Every action in the system publishes an event that:
1. Gets broadcast to all WebSocket clients for that group
2. Triggers downstream effects (trust score updates, logging, etc.)
3. Is persisted for audit/analytics
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Use the redis_client module for consistent Redis URL handling
from shared.redis_client import REDIS_URL


class EventType(str, Enum):
    """All event types in the system."""
    
    # Message events
    MESSAGE_NEW = "message_new"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_DELETED = "message_deleted"
    MESSAGE_RESTORED = "message_restored"
    
    # Member events
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    MEMBER_KICKED = "member_kicked"
    MEMBER_BANNED = "member_banned"
    MEMBER_UNBANNED = "member_unbanned"
    MEMBER_MUTED = "member_muted"
    MEMBER_UNMUTED = "member_unmuted"
    MEMBER_WARNED = "member_warned"
    MEMBER_WARN_REMOVED = "member_warn_removed"
    MEMBER_PROMOTED = "member_promoted"
    MEMBER_DEMOTED = "member_demoted"
    MEMBER_APPROVED = "member_approved"
    MEMBER_TRUST_CHANGED = "member_trust_changed"
    MEMBER_XP_CHANGED = "member_xp_changed"
    MEMBER_LEVEL_UP = "member_level_up"
    MEMBER_PROFILE_UPDATED = "member_profile_updated"
    
    # Moderation events
    MOD_ACTION = "mod_action"
    MOD_ACTION_REVERSED = "mod_action_reversed"
    FLOOD_DETECTED = "flood_detected"
    RAID_DETECTED = "raid_detected"
    WORD_FILTER_TRIGGERED = "word_filter_triggered"
    LOCK_VIOLATION = "lock_violation"
    AI_FLAGGED = "ai_flagged"
    
    # Content events
    CONTENT_BLOCKED = "content_blocked"
    CONTENT_APPROVED = "content_approved"
    
    # Economy events
    COINS_EARNED = "coins_earned"
    COINS_SPENT = "coins_spent"
    COINS_TRANSFERRED = "coins_transferred"
    COINS_ADMIN_GRANTED = "coins_admin_granted"
    COINS_ADMIN_REVOKED = "coins_admin_revoked"
    BONUS_EVENT_STARTED = "bonus_event_started"
    BONUS_EVENT_ENDED = "bonus_event_ended"
    
    # Game events
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    GAME_WON = "game_won"
    
    # Reputation events
    REPUTATION_GIVEN = "reputation_given"
    REPUTATION_TAKEN = "reputation_taken"
    
    # Badge events
    BADGE_EARNED = "badge_earned"
    BADGE_REVOKED = "badge_revoked"
    
    # Module events
    MODULE_ENABLED = "module_enabled"
    MODULE_DISABLED = "module_disabled"
    MODULE_CONFIG_CHANGED = "module_config_changed"
    
    # Lock events
    LOCK_ENABLED = "lock_enabled"
    LOCK_DISABLED = "lock_disabled"
    LOCK_TIMED_STARTED = "lock_timed_started"
    LOCK_TIMED_ENDED = "lock_timed_ended"
    
    # Filter/Note events
    FILTER_ADDED = "filter_added"
    FILTER_REMOVED = "filter_removed"
    FILTER_TRIGGERED = "filter_triggered"
    NOTE_ADDED = "note_added"
    NOTE_REMOVED = "note_removed"
    
    # Scheduler events
    SCHEDULED_MESSAGE_SENT = "scheduled_message_sent"
    SCHEDULED_MESSAGE_CREATED = "scheduled_message_created"
    SCHEDULED_MESSAGE_UPDATED = "scheduled_message_updated"
    SCHEDULED_MESSAGE_DELETED = "scheduled_message_deleted"
    
    # Welcome/Rule events
    WELCOME_SENT = "welcome_sent"
    GOODBYE_SENT = "goodbye_sent"
    RULES_UPDATED = "rules_updated"
    
    # Captcha events
    CAPTCHA_REQUIRED = "captcha_required"
    CAPTCHA_COMPLETED = "captcha_completed"
    CAPTCHA_FAILED = "captcha_failed"
    
    # Challenge events
    CHALLENGE_STARTED = "challenge_started"
    CHALLENGE_PROGRESS = "challenge_progress"
    CHALLENGE_COMPLETED = "challenge_completed"
    
    # Event/RSVP events
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_STARTED = "event_started"
    EVENT_COMPLETED = "event_completed"
    EVENT_RSVP = "event_rsvp"
    
    # Federation events
    FEDERATION_BAN_ISSUED = "federation_ban_issued"
    FEDERATION_BAN_REVOKED = "federation_ban_revoked"
    FEDERATION_GROUP_JOINED = "federation_group_joined"
    FEDERATION_GROUP_LEFT = "federation_group_left"
    
    # Group events
    GROUP_SETTINGS_CHANGED = "group_settings_changed"
    GROUP_LOG_CHANNEL_SET = "group_log_channel_set"
    
    # System events
    SYSTEM_ERROR = "system_error"
    MODULE_HEALTH_CHECK_FAILED = "module_health_check_failed"
    MODULE_HEALTH_CHECK_PASSED = "module_health_check_passed"


@dataclass
class NexusEvent:
    """Event data structure for all system events."""
    
    event_type: EventType
    group_id: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_id: str = field(default_factory=lambda: os.urandom(8).hex())
    
    # Actor (who triggered the event)
    actor_id: Optional[int] = None
    actor_telegram_id: Optional[int] = None
    actor_name: Optional[str] = None
    
    # Target (who/what the event affects)
    target_id: Optional[int] = None
    target_telegram_id: Optional[int] = None
    target_name: Optional[str] = None
    
    # Event details
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    message_id: Optional[int] = None
    channel_id: Optional[int] = None
    
    # Moderation context
    reason: Optional[str] = None
    duration_seconds: Optional[int] = None
    silent: bool = False
    
    # AI context
    ai_inferred: bool = False
    ai_confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        result = asdict(self)
        result["event_type"] = self.event_type.value
        return result
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NexusEvent":
        """Create event from dictionary."""
        data["event_type"] = EventType(data["event_type"])
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "NexusEvent":
        """Create event from JSON string."""
        return cls.from_dict(json.loads(json_str))


class EventBus:
    """
    Central event bus for real-time event broadcasting.
    
    Uses Redis pub/sub for cross-service communication.
    Every event is published to a group-specific channel and
    broadcast to all connected WebSocket clients.
    """
    
    def __init__(self, redis: aioredis.Redis):
        self._redis = redis
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._subscribers: Dict[str, Set[Callable[[NexusEvent], Coroutine]]] = {}
        self._running = False
        
    @staticmethod
    def _get_channel_name(group_id: int) -> str:
        """Get Redis channel name for a group."""
        return f"nexus:events:g{group_id}"
    
    @staticmethod
    def _get_global_channel() -> str:
        """Get global broadcast channel."""
        return "nexus:events:global"
    
    async def publish(self, event: NexusEvent) -> int:
        """
        Publish an event to the event bus.
        
        The event is sent to:
        1. The group-specific channel
        2. The global channel (for system-wide listeners)
        
        Returns the number of clients that received the message.
        """
        channel = self._get_channel_name(event.group_id)
        message = event.to_json()
        
        try:
            # Publish to group channel
            result = await self._redis.publish(channel, message)
            
            # Also publish to global channel for system listeners
            await self._redis.publish(self._get_global_channel(), message)
            
            logger.debug(
                f"Published {event.event_type.value} to {channel} "
                f"(received by {result} clients)"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return 0
    
    async def subscribe(
        self,
        group_id: int,
        callback: Callable[[NexusEvent], Coroutine]
    ) -> None:
        """
        Subscribe to events for a specific group.
        
        The callback will be called for each event received.
        """
        channel = self._get_channel_name(group_id)
        
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
            
            # Subscribe to Redis channel
            if self._pubsub is None:
                self._pubsub = self._redis.pubsub()
            
            await self._pubsub.subscribe(channel)
            logger.info(f"Subscribed to events for group {group_id}")
        
        self._subscribers[channel].add(callback)
    
    async def unsubscribe(
        self,
        group_id: int,
        callback: Callable[[NexusEvent], Coroutine]
    ) -> None:
        """Unsubscribe from events for a specific group."""
        channel = self._get_channel_name(group_id)
        
        if channel in self._subscribers:
            self._subscribers[channel].discard(callback)
            
            if not self._subscribers[channel]:
                del self._subscribers[channel]
                if self._pubsub:
                    await self._pubsub.unsubscribe(channel)
                    logger.info(f"Unsubscribed from events for group {group_id}")
    
    async def start_listener(self) -> None:
        """Start the background listener for Redis pub/sub messages."""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting event bus listener")
        
        # Create pubsub if not exists
        if self._pubsub is None:
            self._pubsub = self._redis.pubsub()
        
        # Subscribe to global channel
        await self._pubsub.subscribe(self._get_global_channel())
        
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                
                if message:
                    await self._handle_message(message)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
                await asyncio.sleep(0.1)
    
    async def stop_listener(self) -> None:
        """Stop the background listener."""
        self._running = False
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None
        logger.info("Event bus listener stopped")
    
    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle a Redis pub/sub message."""
        if message["type"] != "message":
            return
        
        try:
            channel = message["channel"]
            if isinstance(channel, bytes):
                channel = channel.decode("utf-8")
            
            data = message["data"]
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            
            event = NexusEvent.from_json(data)
            
            # Notify all subscribers for this channel
            if channel in self._subscribers:
                for callback in self._subscribers[channel]:
                    try:
                        await callback(event)
                    except Exception as e:
                        logger.error(f"Error in event callback: {e}")
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _event_bus
    
    if _event_bus is None:
        from shared.redis_client import get_redis
        redis = await get_redis()
        _event_bus = EventBus(redis)
    
    return _event_bus


async def publish_event(event: NexusEvent) -> int:
    """Convenience function to publish an event."""
    bus = await get_event_bus()
    return await bus.publish(event)


# Import asyncio at the end to avoid circular imports
import asyncio
