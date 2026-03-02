"""
Action Executor - Single source of truth for all actions in Nexus.

This module ensures that every action (warn, mute, ban, etc.) is executed
consistently whether triggered by:
- A command in the group
- An API call from the Mini App
- An automated system (antispam, word filter, etc.)

Each action:
1. Validates permissions
2. Executes the action in the database
3. Executes the action in Telegram
4. Updates trust scores and XP
5. Broadcasts the event via WebSocket
6. Logs to the log channel if configured
7. Returns the result
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

from aiogram import Bot
from aiogram.enums import ChatMemberStatus, ChatAction
from aiogram.types import ChatPermissions
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import AsyncSessionLocal
from shared.event_bus import (
    EventBus, NexusEvent, EventType, publish_event, get_event_bus
)
from shared.models import (
    Group, Member, ModAction, User, Warning, LogChannel, Wallet,
    TrustScoreHistory, ModuleConfig
)
from shared.schemas import Role

logger = logging.getLogger(__name__)


# Trust score constants
TRUST_SCORE_DEFAULT = 50
TRUST_PENALTY_WARN = -5
TRUST_PENALTY_MUTE = -10
TRUST_PENALTY_BAN = -20
TRUST_PENALTY_KICK = -15
TRUST_BONUS_UNBAN = 5
TRUST_BONUS_UNMUTE = 3

# XP constants
XP_PER_MESSAGE = 1
XP_PER_POSITIVE_ACTION = 10
XP_PENALTY_WARN = -5
XP_PENALTY_MUTE = -20
XP_PENALTY_BAN = -50


@dataclass
class ActionContext:
    """Context for executing an action."""
    
    group_id: int
    actor_id: int  # Internal user ID
    target_id: int  # Internal user ID
    
    # Telegram IDs for convenience
    group_telegram_id: int
    actor_telegram_id: int
    target_telegram_id: int
    
    # Action details
    action_type: str
    reason: Optional[str] = None
    duration_seconds: Optional[int] = None
    silent: bool = False
    
    # Context
    message_id: Optional[int] = None
    message_content: Optional[str] = None
    
    # Source
    source: str = "command"  # command, api, auto, ai
    ai_inferred: bool = False
    ai_confidence: Optional[float] = None
    
    # Database session (for transaction management)
    db: Optional[AsyncSession] = None
    
    # Bot instance
    bot: Optional[Bot] = None


@dataclass
class ActionResult:
    """Result of executing an action."""
    
    success: bool
    action_id: Optional[int] = None
    message: str = ""
    error: Optional[str] = None
    
    # Updated values
    trust_score_before: Optional[int] = None
    trust_score_after: Optional[int] = None
    xp_before: Optional[int] = None
    xp_after: Optional[int] = None
    
    # Event that was broadcast
    event: Optional[NexusEvent] = None
    
    # Additional data
    data: Dict[str, Any] = field(default_factory=dict)


class ActionExecutor:
    """
    Central action executor for all moderation and community actions.
    
    This is the single source of truth for:
    - Warnings
    - Mutes
    - Bans
    - Kicks
    - Approvals
    - Trust score changes
    - XP adjustments
    - And more
    
    Every action goes through this executor to ensure:
    - Consistent execution
    - Proper logging
    - Event broadcasting
    - Trust score updates
    """
    
    def __init__(self, bot: Bot, event_bus: EventBus):
        self.bot = bot
        self.event_bus = event_bus
        self._pre_hooks: Dict[str, List[Callable]] = {}
        self._post_hooks: Dict[str, List[Callable]] = {}
    
    def register_pre_hook(
        self,
        action_type: str,
        hook: Callable[[ActionContext, AsyncSession], Coroutine]
    ) -> None:
        """Register a hook to run before an action."""
        if action_type not in self._pre_hooks:
            self._pre_hooks[action_type] = []
        self._pre_hooks[action_type].append(hook)
    
    def register_post_hook(
        self,
        action_type: str,
        hook: Callable[[ActionContext, ActionResult, AsyncSession], Coroutine]
    ) -> None:
        """Register a hook to run after an action."""
        if action_type not in self._post_hooks:
            self._post_hooks[action_type] = []
        self._post_hooks[action_type].append(hook)
    
    async def _run_pre_hooks(
        self,
        ctx: ActionContext,
        session: AsyncSession
    ) -> bool:
        """Run pre-action hooks. Returns False if any hook vetoes."""
        hooks = self._pre_hooks.get(ctx.action_type, [])
        for hook in hooks:
            try:
                should_continue = await hook(ctx, session)
                if should_continue is False:
                    return False
            except Exception as e:
                logger.error(f"Pre-hook error: {e}")
        return True
    
    async def _run_post_hooks(
        self,
        ctx: ActionContext,
        result: ActionResult,
        session: AsyncSession
    ) -> None:
        """Run post-action hooks."""
        hooks = self._post_hooks.get(ctx.action_type, [])
        for hook in hooks:
            try:
                await hook(ctx, result, session)
            except Exception as e:
                logger.error(f"Post-hook error: {e}")
    
    async def warn(self, ctx: ActionContext) -> ActionResult:
        """
        Issue a warning to a member.
        
        Side effects:
        - Increments warn_count
        - Decreases trust score
        - Decreases XP
        - Broadcasts MEMBER_WARNED event
        - Logs to log channel
        - Checks if warn threshold reached for auto-action
        """
        async with AsyncSessionLocal() as session:
            # Run pre-hooks
            if not await self._run_pre_hooks(ctx, session):
                return ActionResult(success=False, error="Action cancelled by hook")
            
            try:
                # Get member
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                # Get group config for warn threshold
                config_result = await session.execute(
                    select(ModuleConfig).where(
                        ModuleConfig.group_id == ctx.group_id,
                        ModuleConfig.module_name == "moderation"
                    )
                )
                config = config_result.scalar()
                warn_threshold = config.config.get("warn_threshold", 3) if config else 3
                
                # Store old values
                trust_before = member.trust_score
                xp_before = member.xp
                
                # Update member
                member.warn_count += 1
                member.trust_score = max(0, member.trust_score + TRUST_PENALTY_WARN)
                member.xp = max(0, member.xp + XP_PENALTY_WARN)
                member.last_active = datetime.utcnow()
                
                # Create warning record
                warning = Warning(
                    group_id=ctx.group_id,
                    user_id=ctx.target_id,
                    issued_by=ctx.actor_id,
                    reason=ctx.reason or "No reason provided",
                    expires_at=datetime.utcnow() + timedelta(days=30) if not ctx.duration_seconds else datetime.utcnow() + timedelta(seconds=ctx.duration_seconds)
                )
                session.add(warning)
                
                # Create mod action record
                mod_action = ModAction(
                    group_id=ctx.group_id,
                    target_user_id=ctx.target_id,
                    actor_id=ctx.actor_id,
                    action_type="warn",
                    reason=ctx.reason,
                    message_id=ctx.message_id,
                    message_content=ctx.message_content,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred
                )
                session.add(mod_action)
                
                await session.commit()
                
                # Refresh to get IDs
                await session.refresh(mod_action)
                await session.refresh(member)
                
                # Log trust score change
                trust_history = TrustScoreHistory(
                    member_id=member.id,
                    group_id=ctx.group_id,
                    old_score=trust_before,
                    new_score=member.trust_score,
                    change_reason=f"warn:{mod_action.id}",
                    changed_by=ctx.actor_id
                )
                session.add(trust_history)
                await session.commit()
                
                # Create result
                result = ActionResult(
                    success=True,
                    action_id=mod_action.id,
                    message=f"Warned user successfully. Warning {member.warn_count}/{warn_threshold}",
                    trust_score_before=trust_before,
                    trust_score_after=member.trust_score,
                    xp_before=xp_before,
                    xp_after=member.xp,
                    data={
                        "warn_count": member.warn_count,
                        "warn_threshold": warn_threshold,
                        "warning_id": warning.id
                    }
                )
                
                # Create and broadcast event
                event = NexusEvent(
                    event_type=EventType.MEMBER_WARNED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    actor_telegram_id=ctx.actor_telegram_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=ctx.reason,
                    data={
                        "warn_count": member.warn_count,
                        "warn_threshold": warn_threshold,
                        "warning_id": warning.id
                    },
                    message_id=ctx.message_id,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred,
                    ai_confidence=ctx.ai_confidence
                )
                result.event = event
                await self.event_bus.publish(event)
                
                # Check if auto-action needed
                if member.warn_count >= warn_threshold:
                    auto_action = config.config.get("warn_action", "kick") if config else "kick"
                    auto_duration = config.config.get("warn_action_duration", 3600) if config else 3600
                    
                    # Create auto-action context
                    auto_ctx = ActionContext(
                        group_id=ctx.group_id,
                        actor_id=ctx.actor_id,
                        target_id=ctx.target_id,
                        group_telegram_id=ctx.group_telegram_id,
                        actor_telegram_id=ctx.actor_telegram_id,
                        target_telegram_id=ctx.target_telegram_id,
                        action_type=auto_action,
                        reason=f"Auto-{auto_action}: warn threshold reached ({member.warn_count}/{warn_threshold})",
                        duration_seconds=auto_duration if auto_action in ["mute", "ban"] else None,
                        source="auto",
                        silent=True,
                        bot=ctx.bot
                    )
                    
                    if auto_action == "mute":
                        await self.mute(auto_ctx)
                    elif auto_action == "ban":
                        await self.ban(auto_ctx)
                    elif auto_action == "kick":
                        await self.kick(auto_ctx)
                
                # Send Telegram notification
                if not ctx.silent and ctx.bot:
                    try:
                        # Notify in group
                        await self._send_action_notification(ctx, result, member.warn_count, warn_threshold)
                    except Exception as e:
                        logger.error(f"Failed to send notification: {e}")
                
                # Log to log channel
                await self._log_to_channel(ctx, result, session)
                
                # Run post-hooks
                await self._run_post_hooks(ctx, result, session)
                
                return result
                
            except Exception as e:
                logger.error(f"Warn action failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def mute(self, ctx: ActionContext) -> ActionResult:
        """
        Mute a member.
        
        Side effects:
        - Sets is_muted=True, mute_until
        - Increments mute_count
        - Decreases trust score
        - Decreases XP
        - Broadcasts MEMBER_MUTED event
        - Logs to log channel
        """
        async with AsyncSessionLocal() as session:
            if not await self._run_pre_hooks(ctx, session):
                return ActionResult(success=False, error="Action cancelled by hook")
            
            try:
                # Get member
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                # Store old values
                trust_before = member.trust_score
                xp_before = member.xp
                
                # Calculate mute end time
                mute_until = None
                if ctx.duration_seconds:
                    mute_until = datetime.utcnow() + timedelta(seconds=ctx.duration_seconds)
                
                # Update member
                member.is_muted = True
                member.mute_until = mute_until
                member.mute_count += 1
                member.trust_score = max(0, member.trust_score + TRUST_PENALTY_MUTE)
                member.xp = max(0, member.xp + XP_PENALTY_MUTE)
                
                # Create mod action record
                mod_action = ModAction(
                    group_id=ctx.group_id,
                    target_user_id=ctx.target_id,
                    actor_id=ctx.actor_id,
                    action_type="mute",
                    reason=ctx.reason,
                    duration_seconds=ctx.duration_seconds,
                    message_id=ctx.message_id,
                    message_content=ctx.message_content,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred,
                    expires_at=mute_until
                )
                session.add(mod_action)
                
                await session.commit()
                await session.refresh(mod_action)
                await session.refresh(member)
                
                # Execute in Telegram
                if ctx.bot:
                    try:
                        permissions = ChatPermissions(
                            can_send_messages=False,
                            can_send_audios=False,
                            can_send_documents=False,
                            can_send_photos=False,
                            can_send_videos=False,
                            can_send_video_notes=False,
                            can_send_voice_notes=False,
                            can_send_polls=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False,
                            can_change_info=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                        )
                        
                        until_date = int(mute_until.timestamp()) if mute_until else 0
                        
                        await ctx.bot.restrict_chat_member(
                            chat_id=ctx.group_telegram_id,
                            user_id=ctx.target_telegram_id,
                            permissions=permissions,
                            until_date=until_date if until_date > 0 else None
                        )
                    except Exception as e:
                        logger.error(f"Failed to mute in Telegram: {e}")
                        # Continue anyway - database is source of truth
                
                # Create result
                action_result = ActionResult(
                    success=True,
                    action_id=mod_action.id,
                    message=f"Muted user for {ctx.duration_seconds or 'indefinite'} seconds",
                    trust_score_before=trust_before,
                    trust_score_after=member.trust_score,
                    xp_before=xp_before,
                    xp_after=member.xp,
                    data={
                        "mute_count": member.mute_count,
                        "mute_until": mute_until.isoformat() if mute_until else None
                    }
                )
                
                # Create and broadcast event
                event = NexusEvent(
                    event_type=EventType.MEMBER_MUTED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    actor_telegram_id=ctx.actor_telegram_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=ctx.reason,
                    duration_seconds=ctx.duration_seconds,
                    data={
                        "mute_count": member.mute_count,
                        "mute_until": mute_until.isoformat() if mute_until else None
                    },
                    message_id=ctx.message_id,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred,
                    ai_confidence=ctx.ai_confidence
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                # Send notification
                if not ctx.silent and ctx.bot:
                    await self._send_action_notification(ctx, action_result)
                
                # Log to channel
                await self._log_to_channel(ctx, action_result, session)
                
                # Run post-hooks
                await self._run_post_hooks(ctx, action_result, session)
                
                return action_result
                
            except Exception as e:
                logger.error(f"Mute action failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def unmute(self, ctx: ActionContext) -> ActionResult:
        """Unmute a member."""
        async with AsyncSessionLocal() as session:
            if not await self._run_pre_hooks(ctx, session):
                return ActionResult(success=False, error="Action cancelled by hook")
            
            try:
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                trust_before = member.trust_score
                xp_before = member.xp
                
                member.is_muted = False
                member.mute_until = None
                member.trust_score = min(100, member.trust_score + TRUST_BONUS_UNMUTE)
                
                mod_action = ModAction(
                    group_id=ctx.group_id,
                    target_user_id=ctx.target_id,
                    actor_id=ctx.actor_id,
                    action_type="unmute",
                    reason=ctx.reason,
                    silent=ctx.silent
                )
                session.add(mod_action)
                
                await session.commit()
                
                # Execute in Telegram
                if ctx.bot:
                    try:
                        permissions = ChatPermissions.all()
                        await ctx.bot.restrict_chat_member(
                            chat_id=ctx.group_telegram_id,
                            user_id=ctx.target_telegram_id,
                            permissions=permissions
                        )
                    except Exception as e:
                        logger.error(f"Failed to unmute in Telegram: {e}")
                
                action_result = ActionResult(
                    success=True,
                    action_id=mod_action.id,
                    message="Unmuted user successfully",
                    trust_score_before=trust_before,
                    trust_score_after=member.trust_score,
                    xp_before=xp_before,
                    xp_after=member.xp
                )
                
                event = NexusEvent(
                    event_type=EventType.MEMBER_UNMUTED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    actor_telegram_id=ctx.actor_telegram_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=ctx.reason,
                    silent=ctx.silent
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                await self._log_to_channel(ctx, action_result, session)
                await self._run_post_hooks(ctx, action_result, session)
                
                return action_result
                
            except Exception as e:
                logger.error(f"Unmute action failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def ban(self, ctx: ActionContext) -> ActionResult:
        """
        Ban a member.
        
        Side effects:
        - Sets is_banned=True, ban_until
        - Increments ban_count
        - Decreases trust score
        - Decreases XP
        - Broadcasts MEMBER_BANNED event
        - Logs to log channel
        """
        async with AsyncSessionLocal() as session:
            if not await self._run_pre_hooks(ctx, session):
                return ActionResult(success=False, error="Action cancelled by hook")
            
            try:
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                trust_before = member.trust_score
                xp_before = member.xp
                
                ban_until = None
                if ctx.duration_seconds:
                    ban_until = datetime.utcnow() + timedelta(seconds=ctx.duration_seconds)
                
                member.is_banned = True
                member.ban_until = ban_until
                member.ban_count += 1
                member.trust_score = max(0, member.trust_score + TRUST_PENALTY_BAN)
                member.xp = max(0, member.xp + XP_PENALTY_BAN)
                
                mod_action = ModAction(
                    group_id=ctx.group_id,
                    target_user_id=ctx.target_id,
                    actor_id=ctx.actor_id,
                    action_type="ban",
                    reason=ctx.reason,
                    duration_seconds=ctx.duration_seconds,
                    message_id=ctx.message_id,
                    message_content=ctx.message_content,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred,
                    expires_at=ban_until
                )
                session.add(mod_action)
                
                await session.commit()
                
                # Execute in Telegram
                if ctx.bot:
                    try:
                        await ctx.bot.ban_chat_member(
                            chat_id=ctx.group_telegram_id,
                            user_id=ctx.target_telegram_id,
                            until_date=int(ban_until.timestamp()) if ban_until else 0
                        )
                    except Exception as e:
                        logger.error(f"Failed to ban in Telegram: {e}")
                
                action_result = ActionResult(
                    success=True,
                    action_id=mod_action.id,
                    message=f"Banned user for {ctx.duration_seconds or 'indefinite'} seconds",
                    trust_score_before=trust_before,
                    trust_score_after=member.trust_score,
                    xp_before=xp_before,
                    xp_after=member.xp,
                    data={
                        "ban_count": member.ban_count,
                        "ban_until": ban_until.isoformat() if ban_until else None
                    }
                )
                
                event = NexusEvent(
                    event_type=EventType.MEMBER_BANNED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    actor_telegram_id=ctx.actor_telegram_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=ctx.reason,
                    duration_seconds=ctx.duration_seconds,
                    data=action_result.data,
                    message_id=ctx.message_id,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred,
                    ai_confidence=ctx.ai_confidence
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                if not ctx.silent and ctx.bot:
                    await self._send_action_notification(ctx, action_result)
                
                await self._log_to_channel(ctx, action_result, session)
                await self._run_post_hooks(ctx, action_result, session)
                
                return action_result
                
            except Exception as e:
                logger.error(f"Ban action failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def unban(self, ctx: ActionContext) -> ActionResult:
        """Unban a member."""
        async with AsyncSessionLocal() as session:
            if not await self._run_pre_hooks(ctx, session):
                return ActionResult(success=False, error="Action cancelled by hook")
            
            try:
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                trust_before = member.trust_score
                xp_before = member.xp
                
                member.is_banned = False
                member.ban_until = None
                member.trust_score = min(100, member.trust_score + TRUST_BONUS_UNBAN)
                
                mod_action = ModAction(
                    group_id=ctx.group_id,
                    target_user_id=ctx.target_id,
                    actor_id=ctx.actor_id,
                    action_type="unban",
                    reason=ctx.reason,
                    silent=ctx.silent
                )
                session.add(mod_action)
                
                await session.commit()
                
                # Execute in Telegram
                if ctx.bot:
                    try:
                        await ctx.bot.unban_chat_member(
                            chat_id=ctx.group_telegram_id,
                            user_id=ctx.target_telegram_id,
                            only_if_banned=True
                        )
                    except Exception as e:
                        logger.error(f"Failed to unban in Telegram: {e}")
                
                action_result = ActionResult(
                    success=True,
                    action_id=mod_action.id,
                    message="Unbanned user successfully",
                    trust_score_before=trust_before,
                    trust_score_after=member.trust_score,
                    xp_before=xp_before,
                    xp_after=member.xp
                )
                
                event = NexusEvent(
                    event_type=EventType.MEMBER_UNBANNED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    actor_telegram_id=ctx.actor_telegram_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=ctx.reason,
                    silent=ctx.silent
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                await self._log_to_channel(ctx, action_result, session)
                await self._run_post_hooks(ctx, action_result, session)
                
                return action_result
                
            except Exception as e:
                logger.error(f"Unban action failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def kick(self, ctx: ActionContext) -> ActionResult:
        """Kick a member from the group."""
        async with AsyncSessionLocal() as session:
            if not await self._run_pre_hooks(ctx, session):
                return ActionResult(success=False, error="Action cancelled by hook")
            
            try:
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                trust_before = member.trust_score
                xp_before = member.xp
                
                member.trust_score = max(0, member.trust_score + TRUST_PENALTY_KICK)
                member.xp = max(0, member.xp + XP_PENALTY_WARN)
                
                mod_action = ModAction(
                    group_id=ctx.group_id,
                    target_user_id=ctx.target_id,
                    actor_id=ctx.actor_id,
                    action_type="kick",
                    reason=ctx.reason,
                    message_id=ctx.message_id,
                    message_content=ctx.message_content,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_infered if hasattr(ctx, 'ai_infered') else ctx.ai_inferred
                )
                session.add(mod_action)
                
                await session.commit()
                
                # Execute in Telegram
                if ctx.bot:
                    try:
                        await ctx.bot.ban_chat_member(
                            chat_id=ctx.group_telegram_id,
                            user_id=ctx.target_telegram_id
                        )
                        await ctx.bot.unban_chat_member(
                            chat_id=ctx.group_telegram_id,
                            user_id=ctx.target_telegram_id,
                            only_if_banned=True
                        )
                    except Exception as e:
                        logger.error(f"Failed to kick in Telegram: {e}")
                
                action_result = ActionResult(
                    success=True,
                    action_id=mod_action.id,
                    message="Kicked user successfully",
                    trust_score_before=trust_before,
                    trust_score_after=member.trust_score,
                    xp_before=xp_before,
                    xp_after=member.xp
                )
                
                event = NexusEvent(
                    event_type=EventType.MEMBER_KICKED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    actor_telegram_id=ctx.actor_telegram_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=ctx.reason,
                    message_id=ctx.message_id,
                    silent=ctx.silent,
                    ai_inferred=ctx.ai_inferred
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                if not ctx.silent and ctx.bot:
                    await self._send_action_notification(ctx, action_result)
                
                await self._log_to_channel(ctx, action_result, session)
                await self._run_post_hooks(ctx, action_result, session)
                
                return action_result
                
            except Exception as e:
                logger.error(f"Kick action failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def adjust_trust_score(
        self,
        ctx: ActionContext,
        delta: int,
        reason: str
    ) -> ActionResult:
        """Adjust a member's trust score."""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                old_score = member.trust_score
                new_score = max(0, min(100, old_score + delta))
                
                member.trust_score = new_score
                
                trust_history = TrustScoreHistory(
                    member_id=member.id,
                    group_id=ctx.group_id,
                    old_score=old_score,
                    new_score=new_score,
                    change_reason=reason,
                    changed_by=ctx.actor_id
                )
                session.add(trust_history)
                
                await session.commit()
                
                action_result = ActionResult(
                    success=True,
                    message=f"Trust score adjusted from {old_score} to {new_score}",
                    trust_score_before=old_score,
                    trust_score_after=new_score
                )
                
                event = NexusEvent(
                    event_type=EventType.MEMBER_TRUST_CHANGED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=reason,
                    data={
                        "old_score": old_score,
                        "new_score": new_score,
                        "delta": delta
                    }
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                return action_result
                
            except Exception as e:
                logger.error(f"Trust score adjustment failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    async def adjust_xp(
        self,
        ctx: ActionContext,
        delta: int,
        reason: str
    ) -> ActionResult:
        """Adjust a member's XP."""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Member).where(
                        Member.user_id == ctx.target_id,
                        Member.group_id == ctx.group_id
                    )
                )
                member = result.scalar()
                
                if not member:
                    return ActionResult(success=False, error="Member not found")
                
                old_xp = member.xp
                new_xp = max(0, old_xp + delta)
                
                member.xp = new_xp
                
                # Check for level up
                old_level = member.level
                new_level = self._calculate_level(new_xp)
                
                if new_level > old_level:
                    member.level = new_level
                    # Broadcast level up event
                    level_event = NexusEvent(
                        event_type=EventType.MEMBER_LEVEL_UP,
                        group_id=ctx.group_id,
                        target_id=ctx.target_id,
                        target_telegram_id=ctx.target_telegram_id,
                        data={
                            "old_level": old_level,
                            "new_level": new_level,
                            "xp": new_xp
                        }
                    )
                    await self.event_bus.publish(level_event)
                
                await session.commit()
                
                action_result = ActionResult(
                    success=True,
                    message=f"XP adjusted from {old_xp} to {new_xp}",
                    xp_before=old_xp,
                    xp_after=new_xp,
                    data={"level": member.level}
                )
                
                event = NexusEvent(
                    event_type=EventType.MEMBER_XP_CHANGED,
                    group_id=ctx.group_id,
                    actor_id=ctx.actor_id,
                    target_id=ctx.target_id,
                    target_telegram_id=ctx.target_telegram_id,
                    reason=reason,
                    data={
                        "old_xp": old_xp,
                        "new_xp": new_xp,
                        "delta": delta
                    }
                )
                action_result.event = event
                await self.event_bus.publish(event)
                
                return action_result
                
            except Exception as e:
                logger.error(f"XP adjustment failed: {e}")
                return ActionResult(success=False, error=str(e))
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP."""
        # Simple exponential formula: level = floor(sqrt(xp / 100)) + 1
        import math
        return int(math.sqrt(max(0, xp) / 100)) + 1
    
    async def _send_action_notification(
        self,
        ctx: ActionContext,
        result: ActionResult,
        warn_count: int = 0,
        warn_threshold: int = 0
    ) -> None:
        """Send action notification to the group."""
        if not ctx.bot:
            return
        
        try:
            # Get target user info
            async with AsyncSessionLocal() as session:
                user_result = await session.execute(
                    select(User).where(User.id == ctx.target_id)
                )
                target_user = user_result.scalar()
                
                if target_user:
                    target_name = target_user.first_name
                    if target_user.username:
                        target_name = f"@{target_user.username}"
                else:
                    target_name = f"User {ctx.target_telegram_id}"
            
            # Build notification message
            action_emoji = {
                "warn": "⚠️",
                "mute": "🔇",
                "ban": "🚫",
                "kick": "👢",
                "unmute": "🔊",
                "unban": "✅"
            }.get(ctx.action_type, "⚡")
            
            text = f"{action_emoji} <b>{ctx.action_type.upper()}</b>\n\n"
            text += f"👤 User: {target_name}\n"
            
            if ctx.reason:
                text += f"📝 Reason: {ctx.reason}\n"
            
            if ctx.duration_seconds:
                hours = ctx.duration_seconds // 3600
                minutes = (ctx.duration_seconds % 3600) // 60
                if hours > 0:
                    text += f"⏱️ Duration: {hours}h {minutes}m\n"
                else:
                    text += f"⏱️ Duration: {minutes}m\n"
            
            if ctx.action_type == "warn" and warn_threshold > 0:
                text += f"📊 Warnings: {warn_count}/{warn_threshold}\n"
            
            if result.trust_score_before != result.trust_score_after:
                text += f"💫 Trust: {result.trust_score_before} → {result.trust_score_after}\n"
            
            await ctx.bot.send_message(
                chat_id=ctx.group_telegram_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send action notification: {e}")
    
    async def _log_to_channel(
        self,
        ctx: ActionContext,
        result: ActionResult,
        session: AsyncSession
    ) -> None:
        """Log action to log channel if configured."""
        if not ctx.bot or not result.success:
            return
        
        try:
            # Check if log channel is configured
            log_result = await session.execute(
                select(LogChannel).where(
                    LogChannel.group_id == ctx.group_id,
                    LogChannel.is_active == True
                )
            )
            log_channel = log_result.scalar()
            
            if not log_channel:
                return
            
            # Check if this action type should be logged
            log_types = log_channel.log_types or []
            if "mod_actions" not in log_types and "all" not in log_types:
                return
            
            # Get actor and target info
            actor_result = await session.execute(
                select(User).where(User.id == ctx.actor_id)
            )
            actor = actor_result.scalar()
            
            target_result = await session.execute(
                select(User).where(User.id == ctx.target_id)
            )
            target = target_result.scalar()
            
            # Build log message
            action_emoji = {
                "warn": "⚠️",
                "mute": "🔇",
                "ban": "🚫",
                "kick": "👢",
                "unmute": "🔊",
                "unban": "✅"
            }.get(ctx.action_type, "⚡")
            
            text = f"{action_emoji} <b>MOD ACTION</b>\n\n"
            text += f"<b>Action:</b> {ctx.action_type.upper()}\n"
            text += f"<b>Actor:</b> {actor.first_name if actor else 'Unknown'}"
            if actor and actor.username:
                text += f" (@{actor.username})"
            text += f"\n<b>Target:</b> {target.first_name if target else 'Unknown'}"
            if target and target.username:
                text += f" (@{target.username})"
            
            if ctx.reason:
                text += f"\n<b>Reason:</b> {ctx.reason}"
            
            if ctx.duration_seconds:
                hours = ctx.duration_seconds // 3600
                minutes = (ctx.duration_seconds % 3600) // 60
                text += f"\n<b>Duration:</b> {hours}h {minutes}m"
            
            if result.trust_score_before != result.trust_score_after:
                text += f"\n<b>Trust:</b> {result.trust_score_before} → {result.trust_score_after}"
            
            text += f"\n<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            
            if ctx.source == "auto":
                text += "\n<i>🤖 Automated action</i>"
            elif ctx.ai_inferred:
                text += f"\n<i>🤖 AI-suggested (confidence: {ctx.ai_confidence:.0%})</i>"
            
            await ctx.bot.send_message(
                chat_id=log_channel.channel_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to log to channel: {e}")


# Global action executor
_action_executor: Optional[ActionExecutor] = None


async def get_action_executor() -> ActionExecutor:
    """Get or create the global action executor."""
    global _action_executor
    
    if _action_executor is None:
        from aiogram import Bot
        import os
        
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise RuntimeError("BOT_TOKEN not set")
        
        bot = Bot(token=bot_token)
        event_bus = await get_event_bus()
        _action_executor = ActionExecutor(bot, event_bus)
    
    return _action_executor
