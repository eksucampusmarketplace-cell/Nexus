"""Shared Action Executor - Single source of truth for all moderation actions."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.message_template_service import (
    MessageContext,
    MessageTemplateService,
)
from shared.models import ModAction, TrustScoreHistory, Warning
from shared.schemas import ActionType

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of a moderation action."""
    success: bool
    action_type: str
    message: str = ""
    error: str = ""
    
    # For warnings
    warn_count: Optional[int] = None
    threshold_reached: bool = False
    
    # For temporary actions
    expires_at: Optional[datetime] = None
    
    # For additional data
    extra_data: Optional[Dict[str, Any]] = None


class SharedActionExecutor:
    """
    Single source of truth for all moderation actions.
    Every command should call this executor - never implement moderation logic directly.
    """
    
    def __init__(self, db: AsyncSession, bot: Any, group_id: int):
        self.db = db
        self.bot = bot
        self.group_id = group_id
        self.message_service = MessageTemplateService(db)
    
    async def warn_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        reason: str,
        silent: bool = False,
    ) -> ActionResult:
        """Execute a warn action."""
        try:
            # Create warning record
            warning = Warning(
                group_id=self.group_id,
                user_id=target_user.id,
                issued_by=actor_user.id,
                reason=reason,
            )
            self.db.add(warning)
            
            # Update member warn count
            target_member.warn_count = (target_member.warn_count or 0) + 1
            warn_count = target_member.warn_count
            
            # Log action
            await self._log_action(
                ActionType.WARN,
                target_user.id,
                actor_user.id,
                reason=reason,
            )
            
            # Check threshold
            from shared.models import ModuleConfig
            result = await self.db.execute(
                f"SELECT config FROM module_configs WHERE group_id = {self.group_id} AND module_name = 'moderation'"
            )
            config_row = result.fetchone()
            config = config_row[0] if config_row else {}
            
            threshold = config.get("warn_threshold", 3)
            threshold_reached = warn_count >= threshold
            
            # Send notification
            if not silent:
                await self._send_moderation_message(
                    "warn.user.notification",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_name=target_user.first_name,
                        user_username=target_user.username or "",
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                        actor_name=actor_user.first_name,
                        reason=reason,
                        warn_count=warn_count,
                        warn_threshold=threshold,
                    ),
                )
            
            # Auto-action if threshold reached
            if threshold_reached:
                action = config.get("warn_action", "mute")
                duration = config.get("warn_duration", 3600)
                
                if action == "mute":
                    await self._apply_temporary_action(
                        target_member, "mute", duration
                    )
                elif action == "kick":
                    await self.kick_user(target_member, actor_member, target_user, "Auto: Too many warnings")
                elif action == "ban":
                    await self.ban_user(target_member, actor_member, target_user, duration, "Auto: Too many warnings")
            
            await self.db.commit()
            
            return ActionResult(
                success=True,
                action_type="warn",
                warn_count=warn_count,
                threshold_reached=threshold_reached,
            )
            
        except Exception as e:
            logger.error(f"Error in warn_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="warn", error=str(e))
    
    async def mute_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        duration: Optional[int],
        reason: str,
        silent: bool = False,
    ) -> ActionResult:
        """Execute a mute action."""
        try:
            expires_at = None
            if duration:
                expires_at = datetime.utcnow() + timedelta(seconds=duration)
                target_member.mute_until = expires_at
            
            target_member.is_muted = True
            target_member.mute_count = (target_member.mute_count or 0) + 1
            
            # Apply Telegram restriction
            await self.bot.restrict_chat_member(
                chat_id=self.group_id,
                user_id=target_user.telegram_id,
                permissions={"can_send_messages": False},
            )
            
            # Log action
            await self._log_action(
                ActionType.MUTE,
                target_user.id,
                actor_user.id,
                reason=reason,
                duration=duration,
            )
            
            # Send notification
            if not silent:
                duration_formatted = self._format_duration(duration) if duration else "permanent"
                await self._send_moderation_message(
                    "mute.user.notification",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_name=target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                        reason=reason,
                        duration=duration or 0,
                        duration_formatted=duration_formatted,
                        expires_at=expires_at.isoformat() if expires_at else "never",
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(
                success=True,
                action_type="mute",
                expires_at=expires_at,
            )
            
        except Exception as e:
            logger.error(f"Error in mute_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="mute", error=str(e))
    
    async def ban_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        duration: Optional[int],
        reason: str,
        silent: bool = False,
    ) -> ActionResult:
        """Execute a ban action."""
        try:
            expires_at = None
            if duration:
                expires_at = datetime.utcnow() + timedelta(seconds=duration)
                target_member.ban_until = expires_at
            
            target_member.is_banned = True
            target_member.ban_count = (target_member.ban_count or 0) + 1
            
            # Apply Telegram ban
            await self.bot.ban_chat_member(
                chat_id=self.group_id,
                user_id=target_user.telegram_id,
                until_date=expires_at,
            )
            
            # Log action
            await self._log_action(
                ActionType.BAN,
                target_user.id,
                actor_user.id,
                reason=reason,
                duration=duration,
            )
            
            # Send notification
            if not silent:
                duration_formatted = self._format_duration(duration) if duration else "permanent"
                await self._send_moderation_message(
                    "ban.user.notification",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_name=target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                        reason=reason,
                        duration=duration or 0,
                        duration_formatted=duration_formatted,
                        expires_at=expires_at.isoformat() if expires_at else "never",
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(
                success=True,
                action_type="ban",
                expires_at=expires_at,
            )
            
        except Exception as e:
            logger.error(f"Error in ban_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="ban", error=str(e))
    
    async def kick_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        reason: str,
        silent: bool = False,
    ) -> ActionResult:
        """Execute a kick action."""
        try:
            # Apply Telegram kick
            await self.bot.ban_chat_member(
                chat_id=self.group_id,
                user_id=target_user.telegram_id,
            )
            await self.bot.unban_chat_member(
                chat_id=self.group_id,
                user_id=target_user.telegram_id,
            )
            
            # Log action
            await self._log_action(
                ActionType.KICK,
                target_user.id,
                actor_user.id,
                reason=reason,
            )
            
            # Send notification
            if not silent:
                await self._send_moderation_message(
                    "kick.user.notification",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_name=target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                        reason=reason,
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(success=True, action_type="kick")
            
        except Exception as e:
            logger.error(f"Error in kick_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="kick", error=str(e))
    
    async def unmute_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        silent: bool = False,
    ) -> ActionResult:
        """Execute an unmute action."""
        try:
            target_member.is_muted = False
            target_member.mute_until = None
            
            # Remove Telegram restriction
            await self.bot.restrict_chat_member(
                chat_id=self.group_id,
                user_id=target_user.telegram_id,
                permissions={
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_other_messages": True,
                },
            )
            
            # Log action
            await self._log_action(
                ActionType.UNMUTE,
                target_user.id,
                actor_user.id,
            )
            
            # Send notification
            if not silent:
                await self._send_moderation_message(
                    "unmute.user.notification",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(success=True, action_type="unmute")
            
        except Exception as e:
            logger.error(f"Error in unmute_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="unmute", error=str(e))
    
    async def unban_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        silent: bool = False,
    ) -> ActionResult:
        """Execute an unban action."""
        try:
            target_member.is_banned = False
            target_member.ban_until = None
            
            # Remove Telegram ban
            await self.bot.unban_chat_member(
                chat_id=self.group_id,
                user_id=target_user.telegram_id,
            )
            
            # Log action
            await self._log_action(
                ActionType.UNBAN,
                target_user.id,
                actor_user.id,
            )
            
            # Send notification
            if not silent:
                await self._send_moderation_message(
                    "unban.user.notification",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(success=True, action_type="unban")
            
        except Exception as e:
            logger.error(f"Error in unban_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="unban", error=str(e))
    
    async def approve_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        silent: bool = False,
    ) -> ActionResult:
        """Approve a user."""
        try:
            target_member.is_approved = True
            
            # Log action
            await self._log_action(
                ActionType.APPROVE,
                target_user.id,
                actor_user.id,
            )
            
            # Send notification
            if not silent:
                await self._send_moderation_message(
                    "approval.approved",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(success=True, action_type="approve")
            
        except Exception as e:
            logger.error(f"Error in approve_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="approve", error=str(e))
    
    async def trust_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        silent: bool = False,
    ) -> ActionResult:
        """Trust a user."""
        try:
            old_score = target_member.trust_score or 50
            target_member.trust_score = min(100, old_score + 10)
            new_score = target_member.trust_score
            
            # Log trust score history
            history = TrustScoreHistory(
                member_id=target_member.id,
                group_id=self.group_id,
                old_score=old_score,
                new_score=new_score,
                change_reason="Manual trust",
                changed_by=actor_user.id,
            )
            self.db.add(history)
            
            # Log action
            await self._log_action(
                ActionType.TRUST,
                target_user.id,
                actor_user.id,
            )
            
            # Send notification
            if not silent:
                await self._send_moderation_message(
                    "trust.trusted",
                    MessageContext(
                        user_mention=target_user.username or target_user.first_name,
                        user_id=target_user.telegram_id,
                        actor_mention=actor_user.username or actor_user.first_name,
                    ),
                )
            
            await self.db.commit()
            
            return ActionResult(success=True, action_type="trust")
            
        except Exception as e:
            logger.error(f"Error in trust_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="trust", error=str(e))
    
    async def free_user(
        self,
        target_member: Any,
        actor_member: Any,
        target_user: Any,
        actor_user: Any,
        silent: bool = False,
    ) -> ActionResult:
        """Remove all restrictions from a user."""
        try:
            was_muted = target_member.is_muted
            was_banned = target_member.is_banned
            
            target_member.is_muted = False
            target_member.is_banned = False
            target_member.mute_until = None
            target_member.ban_until = None
            target_member.role = "member"
            
            # Remove Telegram restrictions if was muted
            if was_muted:
                await self.bot.restrict_chat_member(
                    chat_id=self.group_id,
                    user_id=target_user.telegram_id,
                    permissions={
                        "can_send_messages": True,
                        "can_send_media_messages": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True,
                    },
                )
            
            # Remove Telegram ban if was banned
            if was_banned:
                await self.bot.unban_chat_member(
                    chat_id=self.group_id,
                    user_id=target_user.telegram_id,
                )
            
            # Log actions
            if was_muted:
                await self._log_action(ActionType.UNMUTE, target_user.id, actor_user.id)
            if was_banned:
                await self._log_action(ActionType.UNBAN, target_user.id, actor_user.id)
            
            await self.db.commit()
            
            return ActionResult(success=True, action_type="free")
            
        except Exception as e:
            logger.error(f"Error in free_user: {e}")
            await self.db.rollback()
            return ActionResult(success=False, action_type="free", error=str(e))
    
    async def _apply_temporary_action(
        self,
        target_member: Any,
        action_type: str,
        duration: int,
    ):
        """Apply a temporary action (called internally)."""
        # This would be called for auto-actions after warn threshold
        pass
    
    async def _log_action(
        self,
        action_type: ActionType,
        target_user_id: int,
        actor_user_id: int,
        reason: Optional[str] = None,
        duration: Optional[int] = None,
    ):
        """Log a moderation action."""
        action = ModAction(
            group_id=self.group_id,
            target_user_id=target_user_id,
            actor_id=actor_user_id,
            action_type=action_type.value,
            reason=reason,
            duration_seconds=duration,
        )
        self.db.add(action)
    
    async def _send_moderation_message(
        self,
        identifier: str,
        context: MessageContext,
    ):
        """Send a moderation message using the template system."""
        try:
            result = await self.message_service.render_message(
                self.group_id, identifier, context
            )
            text, template, is_custom = result
            
            if template and not template.is_enabled:
                return  # Message type disabled
            
            destination = template.destination if template else "public"
            
            if destination == "public":
                # This would send to the group - needs chat_id
                pass
            elif destination == "private_user":
                # This would send to the user - needs user telegram_id
                pass
            elif destination == "private_admin":
                # This would send to admins
                pass
            elif destination == "log":
                # This would send to log channel
                pass
                
        except Exception as e:
            logger.error(f"Error sending moderation message: {e}")
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"


    async def delete_message(
        self,
        message_id: int,
        user: Any,
        deleted_by_user: Any,
        deletion_reason: str,
        content: Optional[str] = None,
        content_type: str = "text",
        media_file_id: Optional[str] = None,
        trigger_word: Optional[str] = None,
        lock_type: Optional[str] = None,
        ai_confidence: Optional[float] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        """
        Delete a message and archive it to the Message Graveyard.
        
        This is the single source of truth for all message deletions.
        Every module that needs to delete a message should call this method.
        
        Args:
            message_id: Telegram message ID
            user: User object who sent the message
            deleted_by_user: User object who is deleting (can be bot user for automated deletions)
            deletion_reason: Reason for deletion (word_filter, flood, lock_violation, nsfw, etc.)
            content: Text content of the message (if any)
            content_type: Type of content (text, photo, video, etc.)
            media_file_id: Telegram file ID for media messages
            trigger_word: If word filter, which word triggered it
            lock_type: If lock violation, which lock type
            ai_confidence: If AI moderation, confidence score
            extra_data: Additional metadata
            
        Returns:
            ActionResult with success status
        """
        try:
            # 1. Delete message from Telegram
            try:
                await self.bot.delete_message(
                    chat_id=self.group_id,
                    message_id=message_id
                )
            except Exception as e:
                logger.warning(f"Could not delete message from Telegram: {e}")
                # Continue anyway - might already be deleted
            
            # 2. Create deleted message record (archive to graveyard)
            from shared.models import DeletedMessage
            
            deleted_msg = DeletedMessage(
                group_id=self.group_id,
                message_id=message_id,
                user_id=user.id,
                content=content,
                content_type=content_type,
                media_file_id=media_file_id,
                deletion_reason=deletion_reason,
                deleted_by=deleted_by_user.id,
                can_restore=True,
                trigger_word=trigger_word,
                lock_type=lock_type,
                ai_confidence=ai_confidence,
                extra_data=extra_data,
            )
            self.db.add(deleted_msg)
            
            # 3. Log action
            await self._log_action(
                ActionType.DELETE,
                user.id,
                deleted_by_user.id,
                reason=f"Message deleted: {deletion_reason}",
                message_id=message_id,
                message_content=content[:500] if content else None,  # Truncate for logging
            )
            
            # 4. Update member stats if applicable
            from sqlalchemy import select
            from shared.models import Member
            
            result = await self.db.execute(
                select(Member).where(
                    Member.user_id == user.id,
                    Member.group_id == self.group_id
                )
            )
            member = result.scalar_one_or_none()
            
            if member:
                # Decrease XP for deleted message (if not manual deletion by admin)
                if deletion_reason != "manual" and member.xp > 0:
                    member.xp = max(0, member.xp - 5)
            
            # 5. Commit transaction
            await self.db.commit()
            
            # 6. Broadcast via WebSocket for real-time updates
            await self._broadcast_deletion(deleted_msg, user, deleted_by_user)
            
            logger.info(
                f"Message {message_id} deleted in group {self.group_id} "
                f"by {deleted_by_user.id} for reason: {deletion_reason}"
            )
            
            return ActionResult(
                success=True,
                action_type="delete",
                message=f"Message deleted and archived to graveyard"
            )
            
        except Exception as e:
            logger.error(f"Error in delete_message: {e}", exc_info=True)
            await self.db.rollback()
            return ActionResult(
                success=False,
                action_type="delete",
                error=str(e)
            )
    
    async def restore_message(
        self,
        deleted_message_id: int,
        restored_by_user: Any,
    ) -> ActionResult:
        """
        Restore a deleted message from the graveyard.
        
        Re-sends the message to the group and marks it as restored.
        Note: Media messages cannot be fully restored as Telegram doesn't allow
        bots to re-send media with original attribution.
        
        Args:
            deleted_message_id: ID of the DeletedMessage record
            restored_by_user: User object who is restoring
            
        Returns:
            ActionResult with success status and new message ID
        """
        try:
            from sqlalchemy import select
            from shared.models import DeletedMessage
            
            # 1. Get deleted message record
            result = await self.db.execute(
                select(DeletedMessage).where(DeletedMessage.id == deleted_message_id)
            )
            deleted_msg = result.scalar_one_or_none()
            
            if not deleted_msg:
                return ActionResult(
                    success=False,
                    action_type="restore",
                    error="Deleted message not found"
                )
            
            if not deleted_msg.can_restore:
                return ActionResult(
                    success=False,
                    action_type="restore",
                    error="Message cannot be restored"
                )
            
            if deleted_msg.restored_at:
                return ActionResult(
                    success=False,
                    action_type="restore",
                    error="Message already restored"
                )
            
            # 2. Re-send message to group
            try:
                if deleted_msg.content_type == "text" and deleted_msg.content:
                    # Send text message with attribution
                    restored = await self.bot.send_message(
                        chat_id=self.group_id,
                        text=f"🔄 *Restored Message*\n\n{deleted_msg.content}",
                        parse_mode="Markdown"
                    )
                    new_message_id = restored.message_id
                elif deleted_msg.media_file_id:
                    # Try to restore media
                    if deleted_msg.content_type == "photo":
                        restored = await self.bot.send_photo(
                            chat_id=self.group_id,
                            photo=deleted_msg.media_file_id,
                            caption=f"🔄 Restored photo"
                        )
                    elif deleted_msg.content_type == "video":
                        restored = await self.bot.send_video(
                            chat_id=self.group_id,
                            video=deleted_msg.media_file_id,
                            caption=f"🔄 Restored video"
                        )
                    else:
                        return ActionResult(
                            success=False,
                            action_type="restore",
                            error=f"Cannot restore media type: {deleted_msg.content_type}"
                        )
                    new_message_id = restored.message_id
                else:
                    return ActionResult(
                        success=False,
                        action_type="restore",
                        error="No content to restore"
                    )
                
                # 3. Update deleted message record
                deleted_msg.restored_at = datetime.utcnow()
                deleted_msg.restored_by = restored_by_user.id
                deleted_msg.restored_message_id = new_message_id
                deleted_msg.can_restore = False
                
                # 4. Log restoration
                await self._log_action(
                    ActionType.RESTORE,
                    deleted_msg.user_id,
                    restored_by_user.id,
                    reason=f"Message restored from graveyard",
                    message_id=new_message_id,
                )
                
                await self.db.commit()
                
                # 5. Broadcast restoration
                await self._broadcast_restoration(deleted_msg, restored_by_user)
                
                logger.info(
                    f"Message {deleted_msg.message_id} restored in group {self.group_id} "
                    f"by {restored_by_user.id}, new message ID: {new_message_id}"
                )
                
                return ActionResult(
                    success=True,
                    action_type="restore",
                    message="Message restored successfully",
                    extra_data={"new_message_id": new_message_id}
                )
                
            except Exception as e:
                logger.error(f"Error sending restored message: {e}")
                await self.db.rollback()
                return ActionResult(
                    success=False,
                    action_type="restore",
                    error=f"Failed to send message: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error in restore_message: {e}", exc_info=True)
            await self.db.rollback()
            return ActionResult(
                success=False,
                action_type="restore",
                error=str(e)
            )
    
    async def _broadcast_deletion(self, deleted_msg: Any, user: Any, deleted_by: Any):
        """Broadcast message deletion via WebSocket."""
        try:
            from shared.redis_client import get_redis
            import json
            
            redis = await get_redis()
            
            event_data = {
                "type": "message_deleted",
                "group_id": self.group_id,
                "data": {
                    "id": deleted_msg.id,
                    "message_id": deleted_msg.message_id,
                    "user_id": user.id,
                    "user_username": user.username,
                    "user_first_name": user.first_name,
                    "deletion_reason": deleted_msg.deletion_reason,
                    "deleted_by": deleted_by.id,
                    "deleted_by_username": deleted_by.username,
                    "content_preview": deleted_msg.content[:100] if deleted_msg.content else None,
                    "deleted_at": deleted_msg.deleted_at.isoformat(),
                }
            }
            
            await redis.publish(
                f"nexus:group:{self.group_id}:events",
                json.dumps(event_data)
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting deletion: {e}")
    
    async def _broadcast_restoration(self, deleted_msg: Any, restored_by: Any):
        """Broadcast message restoration via WebSocket."""
        try:
            from shared.redis_client import get_redis
            import json
            
            redis = await get_redis()
            
            event_data = {
                "type": "message_restored",
                "group_id": self.group_id,
                "data": {
                    "id": deleted_msg.id,
                    "original_message_id": deleted_msg.message_id,
                    "new_message_id": deleted_msg.restored_message_id,
                    "restored_by": restored_by.id,
                    "restored_by_username": restored_by.username,
                    "restored_at": deleted_msg.restored_at.isoformat(),
                }
            }
            
            await redis.publish(
                f"nexus:group:{self.group_id}:events",
                json.dumps(event_data)
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting restoration: {e}")
