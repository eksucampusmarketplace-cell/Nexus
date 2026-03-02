"""Message template service for rendering customizable bot messages."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import MessageTemplate, MessageTemplateDefinition


# Standard variable patterns used across all messages
class MessageVariables:
    """Standard variables available in message templates."""
    
    # User-related
    USER_MENTION = "user_mention"
    USER_NAME = "user_name"
    USER_FULLNAME = "user_fullname"
    USER_USERNAME = "user_username"
    USER_ID = "user_id"
    
    # Actor-related (who triggered the action)
    ACTOR_MENTION = "actor_mention"
    ACTOR_NAME = "actor_name"
    ACTOR_USERNAME = "actor_username"
    
    # Group-related
    GROUP_NAME = "group_name"
    GROUP_USERNAME = "group_username"
    GROUP_ID = "group_id"
    
    # Action-related
    ACTION_TYPE = "action_type"
    REASON = "reason"
    DURATION = "duration"
    DURATION_FORMATTED = "duration_formatted"
    
    # Time-related
    TIME = "time"
    DATE = "date"
    TIMESTAMP = "timestamp"
    
    # Count-related
    WARN_COUNT = "warn_count"
    WARN_THRESHOLD = "warn_threshold"
    MESSAGE_COUNT = "message_count"
    TRUST_SCORE = "trust_score"
    LEVEL = "level"
    XP = "xp"
    
    # Moderation specific
    EXPIRES_AT = "expires_at"
    
    # Economy specific
    COINS = "coins"
    COINS_FORMATTED = "coins_formatted"
    BALANCE = "balance"
    DAILY_STREAK = "daily_streak"
    
    # Game specific
    GAME_TYPE = "game_type"
    SCORE = "score"
    PRIZE = "prize"
    WINNER = "winner"
    
    # Captcha specific
    CAPTCHA_CODE = "captcha_code"
    CAPTCHA_URL = "captcha_url"
    TIMEOUT = "timeout"
    
    # Misc
    INVITE_LINK = "invite_link"
    RULES_LINK = "rules_link"


# Mapping from internal variable names to display names for the UI
VARIABLE_DISPLAY_NAMES: Dict[str, str] = {
    MessageVariables.USER_MENTION: "User Mention (@username or name)",
    MessageVariables.USER_NAME: "User First Name",
    MessageVariables.USER_FULLNAME: "User Full Name",
    MessageVariables.USER_USERNAME: "User Username",
    MessageVariables.USER_ID: "User Telegram ID",
    MessageVariables.ACTOR_MENTION: "Admin Mention",
    MessageVariables.ACTOR_NAME: "Admin First Name",
    MessageVariables.ACTOR_USERNAME: "Admin Username",
    MessageVariables.GROUP_NAME: "Group Name",
    MessageVariables.GROUP_USERNAME: "Group Username",
    MessageVariables.GROUP_ID: "Group ID",
    MessageVariables.ACTION_TYPE: "Action Type (warn/mute/ban)",
    MessageVariables.REASON: "Reason for action",
    MessageVariables.DURATION: "Duration (seconds)",
    MessageVariables.DURATION_FORMATTED: "Duration (formatted)",
    MessageVariables.TIME: "Current Time",
    MessageVariables.DATE: "Current Date",
    MessageVariables.TIMESTAMP: "Unix Timestamp",
    MessageVariables.WARN_COUNT: "Warning Count",
    MessageVariables.WARN_THRESHOLD: "Warning Threshold",
    MessageVariables.MESSAGE_COUNT: "Message Count",
    MessageVariables.TRUST_SCORE: "Trust Score",
    MessageVariables.LEVEL: "Level",
    MessageVariables.XP: "Experience Points",
    MessageVariables.EXPIRES_AT: "Expiration Time",
    MessageVariables.COINS: "Coin Amount",
    MessageVariables.COINS_FORMATTED: "Coins (formatted with emoji)",
    MessageVariables.BALANCE: "Wallet Balance",
    MessageVariables.DAILY_STREAK: "Daily Streak Days",
    MessageVariables.GAME_TYPE: "Game Type",
    MessageVariables.SCORE: "Game Score",
    MessageVariables.PRIZE: "Prize Amount",
    MessageVariables.WINNER: "Winner Mention",
    MessageVariables.CAPTCHA_CODE: "Captcha Code",
    MessageVariables.CAPTCHA_URL: "Captcha Image URL",
    MessageVariables.TIMEOUT: "Timeout (seconds)",
    MessageVariables.INVITE_LINK: "Group Invite Link",
    MessageVariables.RULES_LINK: "Group Rules Link",
}


@dataclass
class MessageContext:
    """Context data for rendering a message template."""
    # User context
    user_mention: str = ""
    user_name: str = ""
    user_fullname: str = ""
    user_username: str = ""
    user_id: int = 0
    
    # Actor context
    actor_mention: str = ""
    actor_name: str = ""
    actor_username: str = ""
    
    # Group context
    group_name: str = ""
    group_username: str = ""
    group_id: int = 0
    
    # Action context
    action_type: str = ""
    reason: str = ""
    duration: int = 0
    duration_formatted: str = ""
    
    # Time context
    time: str = ""
    date: str = ""
    timestamp: int = 0
    
    # Count context
    warn_count: int = 0
    warn_threshold: int = 3
    message_count: int = 0
    trust_score: int = 50
    level: int = 1
    xp: int = 0
    
    # Expiration
    expires_at: str = ""
    
    # Economy
    coins: int = 0
    coins_formatted: str = ""
    balance: int = 0
    daily_streak: int = 0
    
    # Game
    game_type: str = ""
    score: int = 0
    prize: int = 0
    winner_mention: str = ""
    
    # Captcha
    captcha_code: str = ""
    captcha_url: str = ""
    timeout: int = 90
    
    # Misc
    invite_link: str = ""
    rules_link: str = ""
    
    # Extra variables for custom use
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}
        
        # Auto-populate time-related if not set
        now = datetime.utcnow()
        if not self.time:
            self.time = now.strftime("%H:%M")
        if not self.date:
            self.date = now.strftime("%Y-%m-%d")
        if not self.timestamp:
            self.timestamp = int(now.timestamp())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for variable substitution."""
        result = {
            "user_mention": self.user_mention,
            "user_name": self.user_name,
            "user_fullname": self.user_fullname,
            "user_username": self.user_username,
            "user_id": str(self.user_id),
            "actor_mention": self.actor_mention,
            "actor_name": self.actor_name,
            "actor_username": self.actor_username,
            "group_name": self.group_name,
            "group_username": self.group_username,
            "group_id": str(self.group_id),
            "action_type": self.action_type,
            "reason": self.reason,
            "duration": str(self.duration),
            "duration_formatted": self.duration_formatted,
            "time": self.time,
            "date": self.date,
            "timestamp": str(self.timestamp),
            "warn_count": str(self.warn_count),
            "warn_threshold": str(self.warn_threshold),
            "message_count": str(self.message_count),
            "trust_score": str(self.trust_score),
            "level": str(self.level),
            "xp": str(self.xp),
            "expires_at": self.expires_at,
            "coins": str(self.coins),
            "coins_formatted": self.coins_formatted,
            "balance": str(self.balance),
            "daily_streak": str(self.daily_streak),
            "game_type": self.game_type,
            "score": str(self.score),
            "prize": str(self.prize),
            "winner_mention": self.winner_mention,
            "captcha_code": self.captcha_code,
            "captcha_url": self.captcha_url,
            "timeout": str(self.timeout),
            "invite_link": self.invite_link,
            "rules_link": self.rules_link,
        }
        result.update(self.extra)
        return result


class MessageTemplateService:
    """Service for managing and rendering message templates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_template(
        self,
        group_id: int,
        identifier: str,
        language: str = "en",
    ) -> Optional[MessageTemplate]:
        """Get a custom message template for a group."""
        result = await self.db.execute(
            select(MessageTemplate).where(
                MessageTemplate.group_id == group_id,
                MessageTemplate.identifier == identifier,
                MessageTemplate.language == language,
                MessageTemplate.is_enabled == True,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_definition(self, identifier: str) -> Optional[MessageTemplateDefinition]:
        """Get the definition of a message template."""
        result = await self.db.execute(
            select(MessageTemplateDefinition).where(
                MessageTemplateDefinition.identifier == identifier,
                MessageTemplateDefinition.is_enabled == True,
            )
        )
        return result.scalar_one_or_none()
    
    async def render_message(
        self,
        group_id: int,
        identifier: str,
        context: MessageContext,
        language: str = "en",
    ) -> tuple[str, Optional[MessageTemplate], bool]:
        """
        Render a message with the given context.
        
        Returns:
            tuple: (rendered_text, template_used, is_custom)
        """
        # First try to get custom template
        template = await self.get_template(group_id, identifier, language)
        
        if template:
            text = self._render_template(template.custom_text, context)
            return text, template, True
        
        # Fall back to default from definition
        definition = await self.get_definition(identifier)
        if definition:
            # Apply tone if set
            text = definition.default_text
            if template and template.tone and definition.tone_variations:
                text = definition.tone_variations.get(template.tone, text)
            text = self._render_template(text, context)
            return text, template, False
        
        # Last resort: return identifier as placeholder with warning
        return f"[{identifier}]", None, False
    
    def _render_template(self, template: str, context: MessageContext) -> str:
        """Render a template string with variables."""
        variables = context.to_dict()
        result = template
        
        # Replace all {variable} patterns
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result
    
    async def get_all_definitions(self) -> List[MessageTemplateDefinition]:
        """Get all message template definitions."""
        result = await self.db.execute(
            select(MessageTemplateDefinition).where(
                MessageTemplateDefinition.is_enabled == True
            ).order_by(MessageTemplateDefinition.sort_order)
        )
        return list(result.scalars().all())
    
    async def get_definitions_by_category(
        self,
        category_slug: str,
    ) -> List[MessageTemplateDefinition]:
        """Get message definitions by category."""
        result = await self.db.execute(
            select(MessageTemplateDefinition).where(
                MessageTemplateDefinition.category_slug == category_slug,
                MessageTemplateDefinition.is_enabled == True,
            ).order_by(MessageTemplateDefinition.sort_order)
        )
        return list(result.scalars().all())
    
    async def get_group_templates(
        self,
        group_id: int,
    ) -> List[MessageTemplate]:
        """Get all custom templates for a group."""
        result = await self.db.execute(
            select(MessageTemplate).where(
                MessageTemplate.group_id == group_id,
            )
        )
        return list(result.scalars().all())
    
    async def save_template(
        self,
        group_id: int,
        identifier: str,
        custom_text: str,
        language: str = "en",
        tone: Optional[str] = None,
        destination: str = "public",
        self_destruct_seconds: Optional[int] = None,
        is_enabled: bool = True,
        created_by: Optional[int] = None,
    ) -> MessageTemplate:
        """Save or update a message template."""
        # Check if exists
        existing = await self.get_template(group_id, identifier, language)
        
        if existing:
            existing.custom_text = custom_text
            existing.tone = tone
            existing.destination = destination
            existing.self_destruct_seconds = self_destruct_seconds
            existing.is_enabled = is_enabled
            await self.db.flush()
            return existing
        
        # Create new
        template = MessageTemplate(
            group_id=group_id,
            identifier=identifier,
            language=language,
            custom_text=custom_text,
            tone=tone,
            destination=destination,
            self_destruct_seconds=self_destruct_seconds,
            is_enabled=is_enabled,
            created_by=created_by,
        )
        self.db.add(template)
        await self.db.flush()
        return template
    
    async def delete_template(
        self,
        group_id: int,
        identifier: str,
        language: str = "en",
    ) -> bool:
        """Delete a custom template."""
        template = await self.get_template(group_id, identifier, language)
        if template:
            await self.db.delete(template)
            await self.db.flush()
            return True
        return False
    
    async def toggle_template(
        self,
        group_id: int,
        identifier: str,
        language: str = "en",
    ) -> Optional[bool]:
        """Toggle a template on/off. Returns new state."""
        template = await self.get_template(group_id, identifier, language)
        if template:
            template.is_enabled = not template.is_enabled
            await self.db.flush()
            return template.is_enabled
        return None


# ============ MESSAGE DEFINITIONS SEED DATA ============


def get_default_message_definitions() -> List[Dict[str, Any]]:
    """Get all default message template definitions for seeding."""
    return [
        # ============ MODERATION MESSAGES ============
        {
            "identifier": "warn.user.notification",
            "category_slug": "moderation",
            "name": "Warn Notification",
            "description": "Sent when a user is warned",
            "default_text": "⚠️ {user_mention} has been warned.\n\n📝 Reason: {reason}\n📊 Warns: {warn_count}/{warn_threshold}",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_user", "private_admin"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "user_name", "user_username", "user_id",
                "actor_mention", "actor_name", "reason",
                "warn_count", "warn_threshold", "group_name", "time"
            ],
            "module_name": "moderation",
        },
        {
            "identifier": "warn.threshold_reached",
            "category_slug": "moderation",
            "name": "Warning Threshold Reached",
            "description": "Sent when a user reaches the warning threshold",
            "default_text": "🚨 {user_mention} has reached {warn_threshold} warnings!\n\n🔧 Auto-action: {action_type}\n⏱️ Duration: {duration_formatted}",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_admin", "log"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "warn_count", "warn_threshold",
                "action_type", "duration_formatted", "reason"
            ],
            "module_name": "moderation",
        },
        {
            "identifier": "mute.user.notification",
            "category_slug": "moderation",
            "name": "Mute Notification",
            "description": "Sent when a user is muted",
            "default_text": "🔇 {user_mention} has been muted.\n\n⏱️ Duration: {duration_formatted}\n📝 Reason: {reason}",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_user", "private_admin"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "user_name", "duration", "duration_formatted",
                "reason", "expires_at", "actor_mention"
            ],
            "module_name": "moderation",
        },
        {
            "identifier": "ban.user.notification",
            "category_slug": "moderation",
            "name": "Ban Notification",
            "description": "Sent when a user is banned",
            "default_text": "🚫 {user_mention} has been banned.\n\n📝 Reason: {reason}\n⏱️ Duration: {duration_formatted}",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_admin", "log"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "reason", "duration_formatted",
                "expires_at", "actor_mention"
            ],
            "module_name": "moderation",
        },
        {
            "identifier": "kick.user.notification",
            "category_slug": "moderation",
            "name": "Kick Notification",
            "description": "Sent when a user is kicked",
            "default_text": "👢 {user_mention} has been kicked from the group.\n\n📝 Reason: {reason}",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_admin", "log"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "reason", "actor_mention"
            ],
            "module_name": "moderation",
        },
        {
            "identifier": "unmute.user.notification",
            "category_slug": "moderation",
            "name": "Unmute Notification",
            "description": "Sent when a user is unmuted",
            "default_text": "🔊 {user_mention} has been unmuted.",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_user", "private_admin"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "actor_mention"],
            "module_name": "moderation",
        },
        {
            "identifier": "unban.user.notification",
            "category_slug": "moderation",
            "name": "Unban Notification",
            "description": "Sent when a user is unbanned",
            "default_text": "✅ {user_mention} has been unbanned and can rejoin the group.",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_user", "private_admin"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["user_mention", "actor_mention"],
            "module_name": "moderation",
        },
        
        # ============ WELCOME & GOODBYE MESSAGES ============
        {
            "identifier": "welcome.new_member",
            "category_slug": "greetings",
            "name": "Welcome Message",
            "description": "Sent when a new member joins the group",
            "default_text": "👋 Welcome {user_mention} to {group_name}!\n\nWe're glad to have you here!",
            "default_tone": "friendly",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "user_name", "user_fullname",
                "user_username", "group_name", "group_username",
                "invite_link", "rules_link"
            ],
            "module_name": "welcome",
        },
        {
            "identifier": "goodbye.member_left",
            "category_slug": "greetings",
            "name": "Goodbye Message",
            "description": "Sent when a member leaves the group",
            "default_text": "👋 Goodbye {user_mention}! We hope to see you again soon.",
            "default_tone": "friendly",
            "allowed_destinations": ["public"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "user_name", "user_fullname", "user_username"
            ],
            "module_name": "welcome",
        },
        
        # ============ CAPTCHA MESSAGES ============
        {
            "identifier": "captcha.prompt",
            "category_slug": "captcha",
            "name": "Captcha Prompt",
            "description": "Sent when a new member needs to complete captcha",
            "default_text": "👋 Welcome {user_mention}!\n\nPlease complete the captcha to access the group.\n\n⏱️ You have {timeout} seconds.",
            "default_tone": "formal",
            "allowed_destinations": ["private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": [
                "user_mention", "user_name", "captcha_code", "captcha_url", "timeout"
            ],
            "module_name": "captcha",
        },
        {
            "identifier": "captcha.success",
            "category_slug": "captcha",
            "name": "Captcha Success",
            "description": "Sent when user completes captcha successfully",
            "default_text": "✅ Verification complete! Welcome to the group, {user_mention}!",
            "default_tone": "friendly",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "user_name"],
            "module_name": "captcha",
        },
        {
            "identifier": "captcha.failed",
            "category_slug": "captcha",
            "name": "Captcha Failed",
            "description": "Sent when user fails captcha",
            "default_text": "❌ Verification failed. You have been removed from the group.",
            "default_tone": "formal",
            "allowed_destinations": ["private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["user_mention"],
            "module_name": "captcha",
        },
        
        # ============ ANTI-SPAM MESSAGES ============
        {
            "identifier": "flood.detected",
            "category_slug": "antispam",
            "name": "Flood Detection",
            "description": "Sent when flood is detected",
            "default_text": "🌊 {user_mention}, please slow down! You're sending messages too fast.",
            "default_tone": "strict",
            "allowed_destinations": ["public"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "user_name"],
            "module_name": "antispam",
        },
        {
            "identifier": "raid.alert",
            "category_slug": "antispam",
            "name": "Raid Alert",
            "description": "Sent when a raid is detected",
            "default_text": "🚨 RAID DETECTED!\n\n{count} users joined in the last {window} seconds.\n\nGroup has been locked down.",
            "default_tone": "strict",
            "allowed_destinations": ["private_admin", "log"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["count", "window", "action_type"],
            "module_name": "antispam",
        },
        {
            "identifier": "wordfilter.deleted",
            "category_slug": "antispam",
            "name": "Word Filter Delete",
            "description": "Sent when a message is deleted due to word filter",
            "default_text": "🗑️ Message deleted due to forbidden content.",
            "default_tone": "formal",
            "allowed_destinations": ["public"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "reason"],
            "module_name": "word_filter",
        },
        
        # ============ ECONOMY MESSAGES ============
        {
            "identifier": "economy.daily_bonus",
            "category_slug": "economy",
            "name": "Daily Bonus",
            "description": "Sent when user claims daily bonus",
            "default_text": "🎁 Daily Bonus Claimed!\n\n💰 +{coins} coins\n🔥 Streak: {daily_streak} days",
            "default_tone": "friendly",
            "allowed_destinations": ["private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": [
                "coins", "coins_formatted", "balance", "daily_streak", "user_mention"
            ],
            "module_name": "economy",
        },
        {
            "identifier": "economy.coin_received",
            "category_slug": "economy",
            "name": "Coins Received",
            "description": "Sent when user receives coins from another",
            "default_text": "💰 You received {coins} coins from {actor_mention}!\n\n💵 New balance: {balance}",
            "default_tone": "friendly",
            "allowed_destinations": ["private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": [
                "coins", "coins_formatted", "balance", "actor_mention"
            ],
            "module_name": "economy",
        },
        {
            "identifier": "economy.level_up",
            "category_slug": "economy",
            "name": "Level Up",
            "description": "Sent when user levels up",
            "default_text": "🎉 {user_mention} leveled up!\n\n⭐ New Level: {level}\n💎 XP: {xp}",
            "default_tone": "friendly",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["user_mention", "level", "xp"],
            "module_name": "economy",
        },
        
        # ============ GAME MESSAGES ============
        {
            "identifier": "game.trivia.question",
            "category_slug": "games",
            "name": "Trivia Question",
            "description": "Sent when a trivia question is asked",
            "default_text": "🧠 Trivia Time!\n\n{question}\n\nReply with the answer!",
            "default_tone": "casual",
            "allowed_destinations": ["public"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["question", "game_type", "score"],
            "module_name": "games",
        },
        {
            "identifier": "game.trivia.correct",
            "category_slug": "games",
            "name": "Trivia Correct Answer",
            "description": "Sent when user answers correctly",
            "default_text": "✅ Correct! {user_mention} got it right!\n\n🏆 +{prize} coins",
            "default_tone": "friendly",
            "allowed_destinations": ["public"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "prize", "score"],
            "module_name": "games",
        },
        {
            "identifier": "game.winner",
            "category_slug": "games",
            "name": "Game Winner",
            "description": "Sent when there's a game winner",
            "default_text": "🏆 {winner_mention} wins!\n\nScore: {score}",
            "default_tone": "friendly",
            "allowed_destinations": ["public"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["winner_mention", "score", "prize", "game_type"],
            "module_name": "games",
        },
        
        # ============ COMMUNITY MESSAGES ============
        {
            "identifier": "reputation.given",
            "category_slug": "community",
            "name": "Reputation Given",
            "description": "Sent when user gives reputation",
            "default_text": "⭐ {actor_mention} gave +1 reputation to {user_mention}!",
            "default_tone": "friendly",
            "allowed_destinations": ["public"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "actor_mention"],
            "module_name": "reputation",
        },
        {
            "identifier": "badge.earned",
            "category_slug": "community",
            "name": "Badge Earned",
            "description": "Sent when user earns a badge",
            "default_text": "🏅 {user_mention} earned a new badge: {badge_name}!",
            "default_tone": "friendly",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["user_mention", "badge_name", "badge_description"],
            "module_name": "community",
        },
        
        # ============ SYSTEM MESSAGES ============
        {
            "identifier": "system.error",
            "category_slug": "system",
            "name": "Error Message",
            "description": "Generic error message",
            "default_text": "❌ An error occurred: {error_message}",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["error_message", "user_mention"],
            "module_name": "core",
        },
        {
            "identifier": "system.rate_limited",
            "category_slug": "system",
            "name": "Rate Limited",
            "description": "Sent when user is rate limited",
            "default_text": "⏳ Please slow down! You're doing that too often.",
            "default_tone": "formal",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": True,
            "supports_variables": True,
            "available_variables": ["user_mention", "retry_after"],
            "module_name": "core",
        },
        
        # ============ APPROVAL MESSAGES ============
        {
            "identifier": "approval.approved",
            "category_slug": "moderation",
            "name": "User Approved",
            "description": "Sent when user is approved",
            "default_text": "✅ {user_mention} has been approved! You now have full access to the group.",
            "default_tone": "friendly",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["user_mention", "actor_mention"],
            "module_name": "moderation",
        },
        {
            "identifier": "trust.trusted",
            "category_slug": "moderation",
            "name": "User Trusted",
            "description": "Sent when user is trusted",
            "default_text": "⭐ {user_mention} has been marked as trusted!",
            "default_tone": "friendly",
            "allowed_destinations": ["public", "private_user"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": ["user_mention", "actor_mention"],
            "module_name": "trust_system",
        },
        
        # ============ MODERATION ACTION CONFIRMATION ============
        {
            "identifier": "modaction.confirmation",
            "category_slug": "moderation",
            "name": "Action Confirmation",
            "description": "Confirmation message before executing destructive action",
            "default_text": "⚠️ Confirm Action\n\n{action_type}: {user_mention}\nReason: {reason}\n\nClick confirm to proceed.",
            "default_tone": "formal",
            "allowed_destinations": ["private_admin"],
            "supports_self_destruct": False,
            "supports_variables": True,
            "available_variables": [
                "action_type", "user_mention", "reason", "duration", "duration_formatted"
            ],
            "module_name": "moderation",
        },
    ]


def get_default_categories() -> List[Dict[str, Any]]:
    """Get default message categories."""
    return [
        {"slug": "moderation", "name": "Moderation", "description": "Warnings, mutes, bans, kicks", "icon": "shield", "sort_order": 1},
        {"slug": "greetings", "name": "Welcome & Goodbye", "description": "Welcome and farewell messages", "icon": "handshake", "sort_order": 2},
        {"slug": "captcha", "name": "Captcha & Verification", "description": "Verification and captcha messages", "icon": "checkmark", "sort_order": 3},
        {"slug": "antispam", "name": "Anti-Spam", "description": "Flood, raid, and word filter messages", "icon": "fire", "sort_order": 4},
        {"slug": "economy", "name": "Economy", "description": "Coins, daily bonus, level up messages", "icon": "coins", "sort_order": 5},
        {"slug": "games", "name": "Games", "description": "Game-related messages", "icon": "gamepad", "sort_order": 6},
        {"slug": "community", "name": "Community", "description": "Reputation, badges, and community events", "icon": "users", "sort_order": 7},
        {"slug": "system", "name": "System", "description": "Error and system messages", "icon": "gear", "sort_order": 8},
    ]
