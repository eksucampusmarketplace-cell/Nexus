"""
Smart Notification System

Telegram's notification system for bots is all or nothing. This system provides
a smart notification layer where admins can configure:
- Which action types trigger notifications
- Volume thresholds for batching
- Delivery channels (group message, private DM, log channel)
- Quiet hours and priority levels
- Digest modes for non-urgent notifications
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Coroutine
import asyncio

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from shared.redis_client import GroupScopedRedis, get_group_redis


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""
    CRITICAL = "critical"  # Immediate delivery
    HIGH = "high"  # Deliver quickly, bypass quiet hours
    NORMAL = "normal"  # Standard delivery
    LOW = "low"  # Batch into digests


class NotificationChannel(str, Enum):
    """Delivery channels for notifications."""
    GROUP = "group"  # Reply in group
    PRIVATE = "private"  # DM to admin
    LOG_CHANNEL = "log_channel"  # Dedicated log channel
    TOPIC = "topic"  # Specific forum topic
    MINI_APP = "mini_app"  # Push to mini app


class ActionCategory(str, Enum):
    """Categories of actions that can trigger notifications."""
    MODERATION = "moderation"  # Warn, mute, ban, kick
    MEMBERSHIP = "membership"  # Join, leave
    MESSAGE = "message"  # Deletions, edits
    SECURITY = "security"  # Spam, flood, raid detection
    SYSTEM = "system"  # Errors, configuration changes
    USER_REPORTS = "user_reports"  # User-submitted reports
    POLL = "poll"  # Poll events
    THREAD = "thread"  # Thread moderation


@dataclass
class QuietHours:
    """Quiet hours configuration."""
    enabled: bool = False
    start_time: time = time(22, 0)  # 10 PM
    end_time: time = time(8, 0)  # 8 AM
    timezone: str = "UTC"
    allow_critical: bool = True  # Allow critical during quiet hours
    
    def is_quiet(self, when: Optional[datetime] = None) -> bool:
        """Check if current time is within quiet hours."""
        if not self.enabled:
            return False
        
        now = when or datetime.utcnow()
        current_time = now.time()
        
        if self.start_time < self.end_time:
            # Same day (e.g., 22:00 to 08:00 doesn't fit here)
            return self.start_time <= current_time <= self.end_time
        else:
            # Overnight (e.g., 22:00 to 08:00)
            return current_time >= self.start_time or current_time <= self.end_time


@dataclass
class NotificationRule:
    """Rule for when and how to send notifications."""
    rule_id: str
    group_id: int
    
    # What triggers this rule
    action_categories: Set[ActionCategory] = field(default_factory=set)
    specific_actions: Set[str] = field(default_factory=set)  # Specific action types
    
    # Conditions
    min_severity: int = 1  # 1-10 scale
    volume_threshold: int = 1  # Min actions to trigger
    time_window_minutes: int = 5  # For volume counting
    
    # How to deliver
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.LOG_CHANNEL])
    
    # Who receives
    target_roles: Set[str] = field(default_factory=lambda: {"owner", "admin"})
    specific_users: Set[int] = field(default_factory=set)
    
    # When
    quiet_hours: QuietHours = field(default_factory=QuietHours)
    digest_mode: bool = False
    digest_schedule: str = "hourly"  # hourly, daily, weekly
    
    # Message template
    template: Optional[str] = None
    include_context: bool = True
    include_actions: bool = True
    
    # Rate limiting
    cooldown_minutes: int = 0
    max_per_hour: int = 100
    
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def matches(
        self,
        category: ActionCategory,
        action: str,
        severity: int,
        user_role: str,
    ) -> bool:
        """Check if this rule matches an action."""
        if not self.enabled:
            return False
        
        if category not in self.action_categories:
            return False
        
        if self.specific_actions and action not in self.specific_actions:
            return False
        
        if severity < self.min_severity:
            return False
        
        if user_role not in self.target_roles and not self.specific_users:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "group_id": self.group_id,
            "action_categories": [c.value for c in self.action_categories],
            "specific_actions": list(self.specific_actions),
            "min_severity": self.min_severity,
            "volume_threshold": self.volume_threshold,
            "time_window_minutes": self.time_window_minutes,
            "priority": self.priority.value,
            "channels": [c.value for c in self.channels],
            "target_roles": list(self.target_roles),
            "specific_users": list(self.specific_users),
            "quiet_hours": {
                "enabled": self.quiet_hours.enabled,
                "start_time": self.quiet_hours.start_time.isoformat(),
                "end_time": self.quiet_hours.end_time.isoformat(),
                "timezone": self.quiet_hours.timezone,
                "allow_critical": self.quiet_hours.allow_critical,
            },
            "digest_mode": self.digest_mode,
            "digest_schedule": self.digest_schedule,
            "template": self.template,
            "include_context": self.include_context,
            "include_actions": self.include_actions,
            "cooldown_minutes": self.cooldown_minutes,
            "max_per_hour": self.max_per_hour,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationRule":
        qh_data = data.get("quiet_hours", {})
        quiet_hours = QuietHours(
            enabled=qh_data.get("enabled", False),
            start_time=time.fromisoformat(qh_data["start_time"]) if qh_data.get("start_time") else time(22, 0),
            end_time=time.fromisoformat(qh_data["end_time"]) if qh_data.get("end_time") else time(8, 0),
            timezone=qh_data.get("timezone", "UTC"),
            allow_critical=qh_data.get("allow_critical", True),
        )
        
        return cls(
            rule_id=data["rule_id"],
            group_id=data["group_id"],
            action_categories={ActionCategory(c) for c in data.get("action_categories", [])},
            specific_actions=set(data.get("specific_actions", [])),
            min_severity=data.get("min_severity", 1),
            volume_threshold=data.get("volume_threshold", 1),
            time_window_minutes=data.get("time_window_minutes", 5),
            priority=NotificationPriority(data.get("priority", "normal")),
            channels=[NotificationChannel(c) for c in data.get("channels", ["log_channel"])],
            target_roles=set(data.get("target_roles", ["owner", "admin"])),
            specific_users=set(data.get("specific_users", [])),
            quiet_hours=quiet_hours,
            digest_mode=data.get("digest_mode", False),
            digest_schedule=data.get("digest_schedule", "hourly"),
            template=data.get("template"),
            include_context=data.get("include_context", True),
            include_actions=data.get("include_actions", True),
            cooldown_minutes=data.get("cooldown_minutes", 0),
            max_per_hour=data.get("max_per_hour", 100),
            enabled=data.get("enabled", True),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class Notification:
    """A notification to be delivered."""
    notification_id: str
    rule_id: Optional[str]
    group_id: int
    
    # Content
    title: str
    message: str
    priority: NotificationPriority
    category: ActionCategory
    action: str
    
    # Context
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    severity: int = 5
    
    # Delivery tracking
    delivered_to: Dict[str, datetime] = field(default_factory=dict)
    failed_channels: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "rule_id": self.rule_id,
            "group_id": self.group_id,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "category": self.category.value,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "context_data": self.context_data,
            "created_at": self.created_at.isoformat(),
            "severity": self.severity,
            "delivered_to": {k: v.isoformat() for k, v in self.delivered_to.items()},
            "failed_channels": self.failed_channels,
        }


@dataclass
class Digest:
    """A digest of multiple notifications."""
    digest_id: str
    group_id: int
    user_id: int
    schedule: str  # hourly, daily, weekly
    
    notifications: List[Notification] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    
    def add(self, notification: Notification):
        """Add a notification to the digest."""
        self.notifications.append(notification)
    
    def is_ready(self) -> bool:
        """Check if digest is ready to be sent."""
        if not self.notifications:
            return False
        
        now = datetime.utcnow()
        elapsed = (now - self.created_at).total_seconds()
        
        thresholds = {
            "hourly": 3600,
            "daily": 86400,
            "weekly": 604800,
        }
        
        return elapsed >= thresholds.get(self.schedule, 3600)
    
    def summarize(self) -> str:
        """Generate a summary of the digest."""
        by_category = {}
        for n in self.notifications:
            cat = n.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        lines = [f"📬 Notification Digest ({len(self.notifications)} items)"]
        lines.append("")
        
        for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
            lines.append(f"• {cat.replace('_', ' ').title()}: {count}")
        
        lines.append("")
        lines.append("Recent items:")
        
        for n in self.notifications[-5:]:
            lines.append(f"  - {n.title}")
        
        return "\n".join(lines)


class NotificationManager:
    """
    Manages notification rules, delivery, and digests.
    """
    
    def __init__(self, redis: GroupScopedRedis):
        self.redis = redis
        self._delivery_handlers: Dict[NotificationChannel, Callable] = {}
        self._batch_queues: Dict[str, List[Notification]] = {}
    
    def _rule_key(self, rule_id: str) -> str:
        return f"notification:rule:{rule_id}"
    
    def _group_rules_key(self) -> str:
        return "notification:rules"
    
    def _notification_key(self, notification_id: str) -> str:
        return f"notification:{notification_id}"
    
    def _digest_key(self, user_id: int, schedule: str) -> str:
        return f"notification:digest:{user_id}:{schedule}"
    
    def _volume_counter_key(self, rule_id: str) -> str:
        return f"notification:volume:{rule_id}"
    
    def _cooldown_key(self, rule_id: str) -> str:
        return f"notification:cooldown:{rule_id}"
    
    async def create_rule(self, rule: NotificationRule) -> NotificationRule:
        """Create or update a notification rule."""
        await self.redis.set_json(
            self._rule_key(rule.rule_id),
            rule.to_dict(),
        )
        await self.redis.sadd(self._group_rules_key(), rule.rule_id)
        return rule
    
    async def get_rule(self, rule_id: str) -> Optional[NotificationRule]:
        """Get a notification rule."""
        data = await self.redis.get_json(self._rule_key(rule_id))
        if not data:
            return None
        return NotificationRule.from_dict(data)
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a notification rule."""
        await self.redis.delete(self._rule_key(rule_id))
        await self.redis.srem(self._group_rules_key(), rule_id)
        return True
    
    async def get_all_rules(self) -> List[NotificationRule]:
        """Get all notification rules for the group."""
        rule_ids = await self.redis.smembers(self._group_rules_key())
        rules = []
        
        for rid in rule_ids:
            rule = await self.get_rule(rid)
            if rule:
                rules.append(rule)
        
        return rules
    
    async def process_action(
        self,
        category: ActionCategory,
        action: str,
        group_id: int,
        severity: int = 5,
        actor_id: Optional[int] = None,
        actor_name: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        user_role: str = "member",
    ) -> List[Notification]:
        """
        Process an action and generate notifications based on rules.
        
        Returns list of notifications that were generated.
        """
        rules = await self.get_all_rules()
        notifications = []
        
        for rule in rules:
            if not rule.matches(category, action, severity, user_role):
                continue
            
            # Check cooldown
            if rule.cooldown_minutes > 0:
                cooldown_key = self._cooldown_key(rule.rule_id)
                if await self.redis.exists(cooldown_key):
                    continue
            
            # Check volume threshold
            if rule.volume_threshold > 1:
                volume_key = self._volume_counter_key(rule.rule_id)
                current = await self.redis.incr(volume_key)
                await self.redis.expire(volume_key, rule.time_window_minutes * 60)
                
                if current < rule.volume_threshold:
                    continue
                # Reset counter after triggering
                await self.redis.delete(volume_key)
            
            # Create notification
            notification = Notification(
                notification_id=f"notif_{group_id}_{datetime.utcnow().timestamp()}",
                rule_id=rule.rule_id,
                group_id=group_id,
                title=self._generate_title(category, action),
                message=self._generate_message(
                    category, action, actor_name, target_name, context_data
                ),
                priority=rule.priority,
                category=category,
                action=action,
                actor_id=actor_id,
                actor_name=actor_name,
                target_id=target_id,
                target_name=target_name,
                context_data=context_data or {},
                severity=severity,
            )
            
            # Check quiet hours
            in_quiet = rule.quiet_hours.is_quiet()
            if in_quiet and rule.priority != NotificationPriority.CRITICAL and not rule.quiet_hours.allow_critical:
                # Queue for later or add to digest
                if rule.digest_mode:
                    await self._add_to_digest(notification, rule)
                continue
            
            # Deliver notification
            if rule.digest_mode:
                await self._add_to_digest(notification, rule)
            else:
                await self._deliver_notification(notification, rule)
            
            notifications.append(notification)
            
            # Set cooldown
            if rule.cooldown_minutes > 0:
                await self.redis.set(
                    self._cooldown_key(rule.rule_id),
                    "1",
                    expire=rule.cooldown_minutes * 60,
                )
        
        return notifications
    
    async def _deliver_notification(
        self,
        notification: Notification,
        rule: NotificationRule,
    ):
        """Deliver a notification through appropriate channels."""
        for channel in rule.channels:
            handler = self._delivery_handlers.get(channel)
            if handler:
                try:
                    await handler(notification, rule)
                    notification.delivered_to[channel.value] = datetime.utcnow()
                except Exception as e:
                    print(f"Failed to deliver to {channel}: {e}")
                    notification.failed_channels.append(channel.value)
        
        # Store notification
        await self.redis.set_json(
            self._notification_key(notification.notification_id),
            notification.to_dict(),
            expire=86400 * 7,  # Keep for 7 days
        )
    
    async def _add_to_digest(
        self,
        notification: Notification,
        rule: NotificationRule,
    ):
        """Add notification to user's digest."""
        for user_id in rule.specific_users:
            digest_key = self._digest_key(user_id, rule.digest_schedule)
            
            # Get or create digest
            digest_data = await self.redis.get_json(digest_key)
            if digest_data:
                digest = Digest(
                    digest_id=digest_data["digest_id"],
                    group_id=digest_data["group_id"],
                    user_id=digest_data["user_id"],
                    schedule=digest_data["schedule"],
                    created_at=datetime.fromisoformat(digest_data["created_at"]),
                )
            else:
                digest = Digest(
                    digest_id=f"digest_{user_id}_{rule.digest_schedule}_{datetime.utcnow().timestamp()}",
                    group_id=rule.group_id,
                    user_id=user_id,
                    schedule=rule.digest_schedule,
                )
            
            digest.add(notification)
            
            # Save digest
            await self.redis.set_json(
                digest_key,
                {
                    "digest_id": digest.digest_id,
                    "group_id": digest.group_id,
                    "user_id": digest.user_id,
                    "schedule": digest.schedule,
                    "created_at": digest.created_at.isoformat(),
                    "notification_ids": [n.notification_id for n in digest.notifications],
                },
                expire=86400 * 2,
            )
    
    async def process_digests(self) -> List[Digest]:
        """Process and send ready digests."""
        # Find all digest keys
        pattern = self._digest_key("*", "*")
        keys = await self.redis.keys(pattern.replace("*", "*"))
        
        sent_digests = []
        
        for key in keys:
            digest_data = await self.redis.get_json(key)
            if not digest_data:
                continue
            
            # Load notifications
            notifications = []
            for nid in digest_data.get("notification_ids", []):
                notif_data = await self.redis.get_json(self._notification_key(nid))
                if notif_data:
                    notifications.append(Notification(**notif_data))
            
            digest = Digest(
                digest_id=digest_data["digest_id"],
                group_id=digest_data["group_id"],
                user_id=digest_data["user_id"],
                schedule=digest_data["schedule"],
                notifications=notifications,
                created_at=datetime.fromisoformat(digest_data["created_at"]),
            )
            
            if digest.is_ready():
                await self._send_digest(digest)
                sent_digests.append(digest)
                await self.redis.delete(key)
        
        return sent_digests
    
    async def _send_digest(self, digest: Digest):
        """Send a digest to the user."""
        handler = self._delivery_handlers.get(NotificationChannel.PRIVATE)
        if handler:
            # Create a mock notification for the digest
            notif = Notification(
                notification_id=digest.digest_id,
                rule_id=None,
                group_id=digest.group_id,
                title=f"📬 Notification Digest ({len(digest.notifications)} items)",
                message=digest.summarize(),
                priority=NotificationPriority.LOW,
                category=ActionCategory.SYSTEM,
                action="digest",
            )
            
            await handler(notif, None)
        
        digest.sent_at = datetime.utcnow()
    
    def register_delivery_handler(
        self,
        channel: NotificationChannel,
        handler: Callable[[Notification, Optional[NotificationRule]], Coroutine]
    ):
        """Register a handler for delivering to a specific channel."""
        self._delivery_handlers[channel] = handler
    
    def _generate_title(self, category: ActionCategory, action: str) -> str:
        """Generate a notification title."""
        icons = {
            ActionCategory.MODERATION: "🛡️",
            ActionCategory.MEMBERSHIP: "👥",
            ActionCategory.MESSAGE: "💬",
            ActionCategory.SECURITY: "🔒",
            ActionCategory.SYSTEM: "⚙️",
            ActionCategory.USER_REPORTS: "📢",
            ActionCategory.POLL: "📊",
            ActionCategory.THREAD: "🧵",
        }
        
        icon = icons.get(category, "📌")
        action_display = action.replace("_", " ").title()
        category_display = category.value.replace("_", " ").title()
        
        return f"{icon} {category_display}: {action_display}"
    
    def _generate_message(
        self,
        category: ActionCategory,
        action: str,
        actor_name: Optional[str],
        target_name: Optional[str],
        context_data: Optional[Dict[str, Any]],
    ) -> str:
        """Generate notification message."""
        parts = []
        
        if actor_name:
            parts.append(f"<b>Actor:</b> {actor_name}")
        
        if target_name:
            parts.append(f"<b>Target:</b> {target_name}")
        
        if context_data:
            for key, value in context_data.items():
                if key not in ("actor_id", "target_id", "group_id"):
                    parts.append(f"<b>{key.replace('_', ' ').title()}:</b> {value}")
        
        return "\n".join(parts) if parts else f"Action: {action}"


class NotificationDelivery:
    """
    Built-in delivery handlers for common channels.
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def to_group(
        self,
        notification: Notification,
        rule: Optional[NotificationRule],
        chat_id: int,
    ):
        """Deliver notification to a group."""
        text = f"<b>{notification.title}</b>\n\n{notification.message}"
        
        if notification.priority == NotificationPriority.CRITICAL:
            text = f"🚨 <b>CRITICAL</b>\n{text}"
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
        )
    
    async def to_private(
        self,
        notification: Notification,
        rule: Optional[NotificationRule],
        user_id: int,
    ):
        """Deliver notification via DM."""
        text = f"<b>{notification.title}</b>\n\n{notification.message}"
        
        # Add action buttons if applicable
        buttons = []
        if notification.category == ActionCategory.MODERATION and notification.target_id:
            buttons.append([
                InlineKeyboardButton(
                    text="View Profile",
                    callback_data=f"user_profile:{notification.target_id}"
                ),
                InlineKeyboardButton(
                    text="Group Settings",
                    callback_data=f"group_settings:{notification.group_id}"
                ),
            ])
        
        markup = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML",
                reply_markup=markup,
            )
        except Exception as e:
            print(f"Failed to send DM to {user_id}: {e}")
    
    async def to_log_channel(
        self,
        notification: Notification,
        rule: Optional[NotificationRule],
        channel_id: int,
    ):
        """Deliver notification to a log channel."""
        emoji_map = {
            NotificationPriority.CRITICAL: "🔴",
            NotificationPriority.HIGH: "🟠",
            NotificationPriority.NORMAL: "🟡",
            NotificationPriority.LOW: "🟢",
        }
        
        emoji = emoji_map.get(notification.priority, "⚪")
        timestamp = notification.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        text = (
            f"{emoji} <b>{notification.title}</b>\n"
            f"<code>{timestamp}</code>\n"
            f"Priority: {notification.priority.value.upper()}\n\n"
            f"{notification.message}"
        )
        
        await self.bot.send_message(
            chat_id=channel_id,
            text=text,
            parse_mode="HTML",
        )


# Factory function for creating notification manager
async def get_notification_manager(group_id: int) -> NotificationManager:
    """Get notification manager for a group."""
    redis = await get_group_redis(group_id)
    return NotificationManager(redis)
