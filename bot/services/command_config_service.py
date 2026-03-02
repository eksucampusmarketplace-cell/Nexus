"""Command configuration service for managing command customizations."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import CommandConfig, CommandDefinition


@dataclass
class CommandSettings:
    """Resolved command settings for execution."""
    command_id: str
    name: str
    aliases: List[str]
    prefix: str
    min_role: str
    admin_only: bool
    cooldown_seconds: int
    delete_trigger: bool
    reply_mode: bool
    pin_mode: str
    is_enabled: bool
    require_confirmation: bool
    allowed_topics: Optional[List[int]] = None
    denied_topics: Optional[List[int]] = None


class CommandConfigService:
    """Service for managing command customizations per group."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_command_definition(self, command_id: str) -> Optional[CommandDefinition]:
        """Get the base definition of a command."""
        result = await self.db.execute(
            select(CommandDefinition).where(
                CommandDefinition.command_id == command_id,
                CommandDefinition.is_enabled == True,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_definitions(self) -> List[CommandDefinition]:
        """Get all command definitions."""
        result = await self.db.execute(
            select(CommandDefinition).where(
                CommandDefinition.is_enabled == True,
            ).order_by(CommandDefinition.sort_order)
        )
        return list(result.scalars().all())
    
    async def get_definitions_by_module(self, module_name: str) -> List[CommandDefinition]:
        """Get command definitions by module."""
        result = await self.db.execute(
            select(CommandDefinition).where(
                CommandDefinition.module_name == module_name,
                CommandDefinition.is_enabled == True,
            ).order_by(CommandDefinition.sort_order)
        )
        return list(result.scalars().all())
    
    async def get_definitions_by_category(self, category: str) -> List[CommandDefinition]:
        """Get command definitions by category."""
        result = await self.db.execute(
            select(CommandDefinition).where(
                CommandDefinition.category == category,
                CommandDefinition.is_enabled == True,
            ).order_by(CommandDefinition.sort_order)
        )
        return list(result.scalars().all())
    
    async def get_group_config(
        self,
        group_id: int,
        command_id: str,
    ) -> Optional[CommandConfig]:
        """Get custom configuration for a command in a group."""
        result = await self.db.execute(
            select(CommandConfig).where(
                CommandConfig.group_id == group_id,
                CommandConfig.command_id == command_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_group_configs(self, group_id: int) -> List[CommandConfig]:
        """Get all custom configurations for a group."""
        result = await self.db.execute(
            select(CommandConfig).where(
                CommandConfig.group_id == group_id,
            )
        )
        return list(result.scalars().all())
    
    async def resolve_command_settings(
        self,
        group_id: int,
        command_id: str,
    ) -> Optional[CommandSettings]:
        """
        Resolve the final settings for a command, merging defaults with custom config.
        """
        definition = await self.get_command_definition(command_id)
        if not definition:
            return None
        
        config = await self.get_group_config(group_id, command_id)
        
        # Merge defaults with custom config
        name = config.custom_name if config and config.custom_name else definition.name
        
        aliases = (
            config.custom_aliases if config and config.custom_aliases 
            else definition.default_aliases
        )
        
        prefix = (
            config.custom_prefix if config and config.custom_prefix is not None
            else definition.default_prefix
        )
        
        min_role = (
            config.min_role if config and config.min_role
            else definition.default_min_role
        )
        
        admin_only = (
            config.admin_only if config and config.admin_only is not None
            else definition.default_admin_only
        )
        
        cooldown_seconds = (
            config.cooldown_seconds if config and config.cooldown_seconds is not None
            else definition.default_cooldown_seconds
        )
        
        delete_trigger = (
            config.delete_trigger if config and config.delete_trigger is not None
            else definition.default_delete_trigger
        )
        
        reply_mode = (
            config.reply_mode if config and config.reply_mode is not None
            else definition.default_reply_mode
        )
        
        pin_mode = (
            config.pin_mode if config and config.pin_mode
            else definition.default_pin_mode
        )
        
        is_enabled = (
            config.is_enabled if config else definition.is_enabled
        )
        
        require_confirmation = (
            config.require_confirmation if config else definition.supports_confirmation
        )
        
        allowed_topics = config.allowed_topics if config and config.allowed_topics else None
        denied_topics = config.denied_topics if config and config.denied_topics else None
        
        return CommandSettings(
            command_id=command_id,
            name=name,
            aliases=aliases,
            prefix=prefix,
            min_role=min_role,
            admin_only=admin_only,
            cooldown_seconds=cooldown_seconds,
            delete_trigger=delete_trigger,
            reply_mode=reply_mode,
            pin_mode=pin_mode,
            is_enabled=is_enabled,
            require_confirmation=require_confirmation,
            allowed_topics=allowed_topics,
            denied_topics=denied_topics,
        )
    
    async def resolve_command_by_input(
        self,
        group_id: int,
        input_text: str,
    ) -> Tuple[Optional[CommandSettings], Optional[str]]:
        """
        Resolve command settings from user input.
        
        Input can be: "!warn", "/warn", "warn", "silence" (alias)
        
        Returns:
            Tuple of (resolved_settings, matched_name)
        """
        input_text = input_text.strip()
        if not input_text:
            return None, None
        
        # Get all definitions
        definitions = await self.get_all_definitions()
        
        # Try to match input against name or aliases
        for definition in definitions:
            settings = await self.resolve_command_settings(group_id, definition.command_id)
            if not settings or not settings.is_enabled:
                continue
            
            # Check primary name
            if settings.name.lower() == input_text.lower():
                return settings, settings.name
            
            # Check aliases
            for alias in settings.aliases:
                if alias.lower() == input_text.lower():
                    return settings, alias
        
        return None, None
    
    async def save_config(
        self,
        group_id: int,
        command_id: str,
        custom_name: Optional[str] = None,
        custom_aliases: Optional[List[str]] = None,
        custom_prefix: Optional[str] = None,
        min_role: Optional[str] = None,
        admin_only: Optional[bool] = None,
        cooldown_seconds: Optional[int] = None,
        allowed_topics: Optional[List[int]] = None,
        denied_topics: Optional[List[int]] = None,
        delete_trigger: Optional[bool] = None,
        reply_mode: Optional[bool] = None,
        pin_mode: Optional[str] = None,
        is_enabled: bool = True,
        require_confirmation: bool = False,
        updated_by: Optional[int] = None,
    ) -> CommandConfig:
        """Save or update command configuration."""
        existing = await self.get_group_config(group_id, command_id)
        
        if existing:
            if custom_name is not None:
                existing.custom_name = custom_name
            if custom_aliases is not None:
                existing.custom_aliases = custom_aliases
            if custom_prefix is not None:
                existing.custom_prefix = custom_prefix
            if min_role is not None:
                existing.min_role = min_role
            if admin_only is not None:
                existing.admin_only = admin_only
            if cooldown_seconds is not None:
                existing.cooldown_seconds = cooldown_seconds
            if allowed_topics is not None:
                existing.allowed_topics = allowed_topics
            if denied_topics is not None:
                existing.denied_topics = denied_topics
            if delete_trigger is not None:
                existing.delete_trigger = delete_trigger
            if reply_mode is not None:
                existing.reply_mode = reply_mode
            if pin_mode is not None:
                existing.pin_mode = pin_mode
            existing.is_enabled = is_enabled
            existing.require_confirmation = require_confirmation
            existing.updated_by = updated_by
            await self.db.flush()
            return existing
        
        config = CommandConfig(
            group_id=group_id,
            command_id=command_id,
            custom_name=custom_name,
            custom_aliases=custom_aliases,
            custom_prefix=custom_prefix,
            min_role=min_role,
            admin_only=admin_only,
            cooldown_seconds=cooldown_seconds,
            allowed_topics=allowed_topics,
            denied_topics=denied_topics,
            delete_trigger=delete_trigger,
            reply_mode=reply_mode,
            pin_mode=pin_mode,
            is_enabled=is_enabled,
            require_confirmation=require_confirmation,
            updated_by=updated_by,
        )
        self.db.add(config)
        await self.db.flush()
        return config
    
    async def delete_config(
        self,
        group_id: int,
        command_id: str,
    ) -> bool:
        """Delete custom command configuration (reset to defaults)."""
        config = await self.get_group_config(group_id, command_id)
        if config:
            await self.db.delete(config)
            await self.db.flush()
            return True
        return False
    
    async def toggle_command(
        self,
        group_id: int,
        command_id: str,
    ) -> Optional[bool]:
        """Toggle command enabled/disabled. Returns new state."""
        config = await self.get_group_config(group_id, command_id)
        if config:
            config.is_enabled = not config.is_enabled
            await self.db.flush()
            return config.is_enabled
        
        # If no custom config, check definition
        definition = await self.get_command_definition(command_id)
        if definition:
            # Create a new config to disable
            await self.save_config(group_id, command_id, is_enabled=False)
            return False
        
        return None
    
    async def check_cooldown(
        self,
        group_id: int,
        user_id: int,
        command_id: str,
    ) -> Tuple[bool, int]:
        """
        Check if command is on cooldown for user.
        
        Returns:
            Tuple of (is_allowed, remaining_seconds)
        """
        from shared.redis_client import GroupScopedRedis
        
        # This would check Redis for cooldown
        # For now, just return allowed
        return True, 0
    
    async def set_cooldown(
        self,
        group_id: int,
        user_id: int,
        command_id: str,
        seconds: int,
    ) -> None:
        """Set cooldown for a command."""
        # This would set Redis key
        pass


# ============ DEFAULT COMMAND DEFINITIONS ============


def get_default_command_definitions() -> List[Dict[str, Any]]:
    """Get all default command definitions for seeding."""
    return [
        # ============ MODERATION COMMANDS ============
        {
            "command_id": "warn",
            "module_name": "moderation",
            "name": "warn",
            "description": "Warn a user for violating rules",
            "category": "moderation",
            "usage": "/warn [user] [reason]",
            "examples": ["/warn @username spam", "/warn 123456789 inappropriate content"],
            "default_prefix": "!",
            "default_aliases": ["w"],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": True,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "warns",
            "module_name": "moderation",
            "name": "warns",
            "description": "View user's warning count",
            "category": "moderation",
            "usage": "/warns [user]",
            "examples": ["/warns @username"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "mute",
            "module_name": "moderation",
            "name": "mute",
            "description": "Mute a user (temporarily restrict sending messages)",
            "category": "moderation",
            "usage": "/mute [user] [duration] [reason]",
            "examples": ["/mute @username 1h spam", "/mute 123456789 30m"],
            "default_prefix": "!",
            "default_aliases": ["m", "tmute", "tm"],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": True,
            "default_delete_trigger": True,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "unmute",
            "module_name": "moderation",
            "name": "unmute",
            "description": "Unmute a previously muted user",
            "category": "moderation",
            "usage": "/unmute [user]",
            "examples": ["/unmute @username"],
            "default_prefix": "!",
            "default_aliases": ["um"],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "ban",
            "module_name": "moderation",
            "name": "ban",
            "description": "Ban a user from the group",
            "category": "moderation",
            "usage": "/ban [user] [duration] [reason]",
            "examples": ["/ban @username spam", "/ban 123456789 7d inappropriate"],
            "default_prefix": "!",
            "default_aliases": ["b", "tban", "tb"],
            "default_min_role": "admin",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": True,
            "default_delete_trigger": True,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "unban",
            "module_name": "moderation",
            "name": "unban",
            "description": "Unban a previously banned user",
            "category": "moderation",
            "usage": "/unban [user]",
            "examples": ["/unban @username"],
            "default_prefix": "!",
            "default_aliases": ["ub"],
            "default_min_role": "admin",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "kick",
            "module_name": "moderation",
            "name": "kick",
            "description": "Kick a user from the group (they can rejoin)",
            "category": "moderation",
            "usage": "/kick [user] [reason]",
            "examples": ["/kick @username behave"],
            "default_prefix": "!",
            "default_aliases": ["k"],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": True,
            "default_delete_trigger": True,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "promote",
            "module_name": "moderation",
            "name": "promote",
            "description": "Promote a user to admin or moderator",
            "category": "moderation",
            "usage": "/promote [user] [role]",
            "examples": ["/promote @username mod", "/promote 123456789 admin"],
            "default_prefix": "!",
            "default_aliases": ["addmod", "addadmin"],
            "default_min_role": "owner",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": False,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "temporary",
        },
        {
            "command_id": "demote",
            "module_name": "moderation",
            "name": "demote",
            "description": "Demote an admin or moderator to regular member",
            "category": "moderation",
            "usage": "/demote [user]",
            "examples": ["/demote @username"],
            "default_prefix": "!",
            "default_aliases": ["rmmod", "rmadmin"],
            "default_min_role": "owner",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": False,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "approve",
            "module_name": "moderation",
            "name": "approve",
            "description": "Approve a user (bypass all restrictions)",
            "category": "moderation",
            "usage": "/approve [user]",
            "examples": ["/approve @username"],
            "default_prefix": "!",
            "default_aliases": ["whitelist"],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "unapprove",
            "module_name": "moderation",
            "name": "unapprove",
            "description": "Remove approval from a user",
            "category": "moderation",
            "usage": "/unapprove [user]",
            "examples": ["/unapprove @username"],
            "default_prefix": "!",
            "default_aliases": ["unwhitelist"],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "trust",
            "module_name": "trust_system",
            "name": "trust",
            "description": "Mark user as trusted (reduces restrictions)",
            "category": "moderation",
            "usage": "/trust [user]",
            "examples": ["/trust @username"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "mod",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        
        # ============ WELCOME COMMANDS ============
        {
            "command_id": "welcome",
            "module_name": "welcome",
            "name": "welcome",
            "description": "Set welcome message for the group",
            "category": "greetings",
            "usage": "/welcome [text]",
            "examples": ["/welcome Welcome to the group!"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "admin",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "goodbye",
            "module_name": "welcome",
            "name": "goodbye",
            "description": "Set goodbye message when members leave",
            "category": "greetings",
            "usage": "/goodbye [text]",
            "examples": ["/goodbye Goodbye {user}!"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "admin",
            "default_cooldown_seconds": 0,
            "default_admin_only": True,
            "supports_cooldown": False,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        
        # ============ ECONOMY COMMANDS ============
        {
            "command_id": "balance",
            "module_name": "economy",
            "name": "balance",
            "description": "Check your coin balance",
            "category": "economy",
            "usage": "/balance [user]",
            "examples": ["/balance", "/balance @username"],
            "default_prefix": "!",
            "default_aliases": ["bal", "coins"],
            "default_min_role": "member",
            "default_cooldown_seconds": 10,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "daily",
            "module_name": "economy",
            "name": "daily",
            "description": "Claim your daily coin bonus",
            "category": "economy",
            "usage": "/daily",
            "examples": ["/daily"],
            "default_prefix": "!",
            "default_aliases": ["dailybonus", "claim"],
            "default_min_role": "member",
            "default_cooldown_seconds": 86400,  # 24 hours
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "leaderboard",
            "module_name": "economy",
            "name": "leaderboard",
            "description": "View the group coin leaderboard",
            "category": "economy",
            "usage": "/leaderboard",
            "examples": ["/leaderboard"],
            "default_prefix": "!",
            "default_aliases": ["top", "lb"],
            "default_min_role": "member",
            "default_cooldown_seconds": 30,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "temporary",
        },
        {
            "command_id": "give",
            "module_name": "economy",
            "name": "give",
            "description": "Give coins to another user",
            "category": "economy",
            "usage": "/give [user] [amount]",
            "examples": ["/give @username 100"],
            "default_prefix": "!",
            "default_aliases": ["pay", "send"],
            "default_min_role": "member",
            "default_cooldown_seconds": 60,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": True,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        
        # ============ GAME COMMANDS ============
        {
            "command_id": "trivia",
            "module_name": "games",
            "name": "trivia",
            "description": "Start a trivia game",
            "category": "games",
            "usage": "/trivia",
            "examples": ["/trivia"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "member",
            "default_cooldown_seconds": 10,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": True,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": False,
            "default_pin_mode": "none",
        },
        {
            "command_id": "guess",
            "module_name": "games",
            "name": "guess",
            "description": "Start a number guessing game",
            "category": "games",
            "usage": "/guess [number]",
            "examples": ["/guess 50"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "member",
            "default_cooldown_seconds": 30,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        
        # ============ UTILITY COMMANDS ============
        {
            "command_id": "info",
            "module_name": "info",
            "name": "info",
            "description": "Get information about a user or the group",
            "category": "utility",
            "usage": "/info [user]",
            "examples": ["/info", "/info @username"],
            "default_prefix": "!",
            "default_aliases": ["i", "who"],
            "default_min_role": "member",
            "default_cooldown_seconds": 5,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": True,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "rules",
            "module_name": "rules",
            "name": "rules",
            "description": "Show group rules",
            "category": "utility",
            "usage": "/rules",
            "examples": ["/rules"],
            "default_prefix": "!",
            "default_aliases": [],
            "default_min_role": "member",
            "default_cooldown_seconds": 10,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": False,
            "supports_prefix_change": True,
            "supports_permission_change": False,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
        {
            "command_id": "notes",
            "module_name": "notes",
            "name": "notes",
            "description": "List or retrieve saved notes",
            "category": "utility",
            "usage": "/notes [keyword]",
            "examples": ["/notes", "/notes rules"],
            "default_prefix": "!",
            "default_aliases": ["snippets", "saved"],
            "default_min_role": "member",
            "default_cooldown_seconds": 5,
            "default_admin_only": False,
            "supports_cooldown": True,
            "supports_aliases": True,
            "supports_prefix_change": True,
            "supports_permission_change": False,
            "supports_topic_restriction": False,
            "supports_confirmation": False,
            "default_delete_trigger": False,
            "default_reply_mode": True,
            "default_pin_mode": "none",
        },
    ]
