"""NexusContext - Central context for all bot operations."""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from aiogram import Bot
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
    ReplyParameters,
    Update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from shared.redis_client import GroupScopedRedis, RateLimiter
from shared.schemas import ActionType, Role

if TYPE_CHECKING:
    pass


@dataclass
class BotIdentity:
    """Bot identity information."""

    bot_id: int
    username: str
    name: str
    token_hash: str


@dataclass
class MemberProfile:
    """Member profile within context."""

    id: int
    user_id: int
    group_id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    role: Role
    trust_score: int
    xp: int
    level: int
    warn_count: int
    is_muted: bool
    is_banned: bool
    is_approved: bool
    is_whitelisted: bool
    joined_at: datetime
    message_count: int
    custom_title: Optional[str]

    @property
    def is_admin(self) -> bool:
        return self.role in (Role.OWNER, Role.ADMIN)

    @property
    def is_moderator(self) -> bool:
        return self.role in (Role.OWNER, Role.ADMIN, Role.MODERATOR)

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        return f"<a href='tg://user?id={self.telegram_id}'>{self.full_name}</a>"


@dataclass
class GroupProfile:
    """Group profile within context."""

    id: int
    telegram_id: int
    title: str
    username: Optional[str]
    language: str
    owner_id: int
    member_count: int
    is_premium: bool
    enabled_modules: List[str]
    module_configs: Dict[str, Dict[str, Any]]


@dataclass
class AIClient:
    """AI client wrapper."""

    api_key: Optional[str] = None
    rate_limit_remaining: int = 100

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
    ) -> str:
        """Complete a prompt using AI."""
        # Placeholder for AI integration
        if not self.api_key:
            return "AI not configured"
        # Actual implementation would call OpenAI API
        return "AI response"

    async def moderate(self, text: str) -> Dict[str, Any]:
        """Check if text is inappropriate."""
        return {"flagged": False, "categories": {}}


@dataclass
class SchedulerClient:
    """Celery scheduler client."""

    async def send_later(
        self,
        chat_id: int,
        text: str,
        when: datetime,
        **kwargs,
    ) -> str:
        """Schedule a message."""
        # Implementation would use Celery
        return "task_id"

    async def schedule_recurring(
        self,
        chat_id: int,
        text: str,
        cron: str,
        **kwargs,
    ) -> str:
        """Schedule a recurring message."""
        return "task_id"


@dataclass
class I18nClient:
    """Internationalization client."""

    language: str = "en"

    def t(self, key: str, **kwargs) -> str:
        """Translate a key."""
        # Placeholder for i18n
        translations = {
            "en": {
                "hello": "Hello {name}!",
                "goodbye": "Goodbye {name}!",
                "warned": "⚠️ {target} has been warned.\nReason: {reason}",
                "muted": "🔇 {target} has been muted for {duration}.\nReason: {reason}",
                "banned": "🚫 {target} has been banned.\nReason: {reason}",
                "kicked": "👢 {target} has been kicked.\nReason: {reason}",
                "no_permission": "❌ You don't have permission to use this command.",
                "user_not_found": "❌ User not found.",
                "invalid_duration": "❌ Invalid duration format. Use: 1m, 1h, 1d, 1w",
                "action_complete": "✅ Action completed successfully.",
            }
        }
        text = translations.get(self.language, translations["en"]).get(key, key)
        return text.format(**kwargs) if kwargs else text


@dataclass
class WarnResult:
    """Result of a warning."""

    success: bool
    warn_count: int
    threshold_reached: bool
    auto_action: Optional[str] = None


@dataclass
class UserHistory:
    """User moderation history."""

    warnings: int
    mutes: int
    bans: int
    kicks: int
    last_warning: Optional[datetime]
    last_mute: Optional[datetime]
    last_ban: Optional[datetime]
    total_messages: int
    trust_score_history: List[Tuple[datetime, int]]


@dataclass
class NexusContext:
    """Central context for all bot operations."""

    # Identity (required)
    bot: Bot
    bot_identity: BotIdentity
    update: Update
    user: MemberProfile  # Required - must come before optional fields
    group: GroupProfile  # Required - must come before optional fields

    # Optional identity
    message: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    inline_query: Optional[InlineQuery] = None
    replied_to: Optional[Message] = None
    target_user: Optional[MemberProfile] = None

    # Parsed command info
    parsed_command: Optional[Any] = None  # ParsedMessage from middleware
    is_deactivate_command: bool = False  # True if !! prefix was used

    # Infrastructure
    ai: AIClient = field(default_factory=AIClient)
    db: Optional[AsyncSession] = None
    cache: Optional[GroupScopedRedis] = None
    scheduler: SchedulerClient = field(default_factory=SchedulerClient)
    i18n: I18nClient = field(default_factory=I18nClient)

    # Internal state
    _rate_limiter: Optional[RateLimiter] = None
    _silent: bool = False

    @classmethod
    async def create(
        cls,
        bot: Bot,
        bot_identity: BotIdentity,
        update: Update,
        user: MemberProfile,
        group: GroupProfile,
        db: AsyncSession,
        cache: GroupScopedRedis,
    ) -> "NexusContext":
        """Create a new context."""
        ctx = cls(
            bot=bot,
            bot_identity=bot_identity,
            update=update,
            user=user,
            group=group,
            db=db,
            cache=cache,
        )

        # Extract message types
        if update.message:
            ctx.message = update.message
            if update.message.reply_to_message:
                ctx.replied_to = update.message.reply_to_message
        elif update.callback_query:
            ctx.callback_query = update.callback_query
        elif update.inline_query:
            ctx.inline_query = update.inline_query

        ctx._rate_limiter = RateLimiter(cache)
        ctx.i18n = I18nClient(language=group.language)
        ctx.ai = AIClient(api_key=os.getenv("OPENAI_API_KEY"))

        return ctx

    def set_target(self, target: MemberProfile) -> None:
        """Set target user for moderation actions."""
        self.target_user = target

    def set_silent(self, silent: bool = True) -> None:
        """Set silent mode for actions."""
        self._silent = silent

    async def check_rate_limit(
        self,
        key: str,
        limit: int = 5,
        window: int = 60,
    ) -> Tuple[bool, int, int]:
        """Check if action is rate limited."""
        if not self._rate_limiter:
            return True, limit, window
        return await self._rate_limiter.is_allowed(key, limit, window)

    async def reply(
        self,
        text: str,
        buttons: Optional[List[List[Dict[str, str]]]] = None,
        delete_after: Optional[int] = None,
        parse_mode: str = "HTML",
        protect: bool = False,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> Message:
        """Reply to the current message."""
        if not self.message:
            raise ValueError("No message to reply to")

        # If reply_markup is not provided, build it from buttons
        if reply_markup is None and buttons:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=btn["text"],
                        url=btn.get("url"),
                        callback_data=btn.get("callback_data"),
                    )
                    for btn in row
                ]
                for row in buttons
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        msg = await self.bot.send_message(
            chat_id=self.message.chat.id,
            text=text,
            reply_parameters=ReplyParameters(message_id=self.message.message_id),
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            protect_content=protect,
        )

        if delete_after:
            await self.scheduler.send_later(
                self.message.chat.id,
                "delete",
                datetime.utcnow() + timedelta(seconds=delete_after),
                message_id=msg.message_id,
            )

        return msg

    async def reply_media(
        self,
        media: Union[str, bytes],
        media_type: str = "photo",
        caption: Optional[str] = None,
        buttons: Optional[List[List[Dict[str, str]]]] = None,
    ) -> Message:
        """Reply with media."""
        if not self.message:
            raise ValueError("No message to reply to")

        reply_markup = None
        if buttons:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text=btn["text"],
                        url=btn.get("url"),
                        callback_data=btn.get("callback_data"),
                    )
                    for btn in row
                ]
                for row in buttons
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        kwargs = {
            "chat_id": self.message.chat.id,
            "caption": caption,
            "reply_markup": reply_markup,
            "reply_parameters": ReplyParameters(message_id=self.message.message_id),
        }

        if media_type == "photo":
            return await self.bot.send_photo(photo=media, **kwargs)
        elif media_type == "video":
            return await self.bot.send_video(video=media, **kwargs)
        elif media_type == "document":
            return await self.bot.send_document(document=media, **kwargs)
        elif media_type == "animation":
            return await self.bot.send_animation(animation=media, **kwargs)
        else:
            raise ValueError(f"Unknown media type: {media_type}")

    async def notify_admins(
        self,
        text: str,
        action_type: Optional[str] = None,
        silent: bool = False,
    ) -> None:
        """Notify admins about an action."""
        if not self.db:
            return

        # Get admins from cache or database
        admin_key = "admins:list"
        admins = await self.cache.get_json(admin_key) if self.cache else None

        if not admins:
            # Query from database

            result = await self.db.execute(f"""
                SELECT m.user_id, u.telegram_id
                FROM members m
                JOIN users u ON m.user_id = u.id
                WHERE m.group_id = {self.group.id}
                AND m.role IN ('owner', 'admin')
                """)
            admins = [{"telegram_id": row[1]} for row in result.fetchall()]
            if self.cache:
                await self.cache.set_json(admin_key, admins, expire=300)

        for admin in admins:
            try:
                await self.bot.send_message(
                    chat_id=admin["telegram_id"],
                    text=text,
                    parse_mode="HTML",
                    disable_notification=silent,
                )
            except Exception:
                pass

    async def log_action(
        self,
        action_type: ActionType,
        target_user: MemberProfile,
        reason: Optional[str] = None,
        duration: Optional[int] = None,
        ai_inferred: bool = False,
        silent: bool = False,
    ) -> None:
        """Log a moderation action."""
        if not self.db:
            return

        from shared.models import ModAction

        action = ModAction(
            group_id=self.group.id,
            target_user_id=target_user.user_id,
            actor_id=self.user.user_id,
            action_type=action_type.value,
            reason=reason,
            duration_seconds=duration,
            silent=silent or self._silent,
            ai_inferred=ai_inferred,
            message_id=self.message.message_id if self.message else None,
            message_content=self.message.text if self.message else None,
        )

        self.db.add(action)
        await self.db.flush()

    async def delete_message(self, message_id: Optional[int] = None) -> bool:
        """Delete a message."""
        if not self.message:
            return False

        try:
            await self.bot.delete_message(
                chat_id=self.message.chat.id,
                message_id=message_id or self.message.message_id,
            )
            return True
        except Exception:
            return False

    async def purge_messages(
        self,
        from_message_id: int,
        to_message_id: int,
    ) -> int:
        """Purge messages in a range."""
        deleted = 0
        for msg_id in range(from_message_id, to_message_id + 1):
            try:
                await self.bot.delete_message(
                    chat_id=self.message.chat.id,
                    message_id=msg_id,
                )
                deleted += 1
            except Exception:
                pass
        return deleted

    async def pin_message(
        self,
        message_id: int,
        notify: bool = True,
    ) -> bool:
        """Pin a message."""
        try:
            await self.bot.pin_chat_message(
                chat_id=self.group.telegram_id,
                message_id=message_id,
                disable_notification=not notify,
            )
            return True
        except Exception:
            return False

    async def warn_user(
        self,
        target: Optional[MemberProfile] = None,
        reason: Optional[str] = None,
        silent: bool = False,
    ) -> WarnResult:
        """Warn a user."""
        target = target or self.target_user
        if not target:
            raise ValueError("No target user")

        if not self.db:
            return WarnResult(False, 0, False)

        from shared.models import Warning

        # Create warning
        warning = Warning(
            group_id=self.group.id,
            user_id=target.user_id,
            issued_by=self.user.user_id,
            reason=reason or "No reason provided",
        )
        self.db.add(warning)

        # Update member
        result = await self.db.execute(f"""
            UPDATE members
            SET warn_count = warn_count + 1
            WHERE id = {target.id}
            RETURNING warn_count
            """)
        warn_count = result.scalar()

        await self.log_action(
            ActionType.WARN,
            target,
            reason,
            silent=silent,
        )

        # Check for auto-action
        threshold_reached = False
        auto_action = None

        # Get config
        config = self.group.module_configs.get("moderation", {})
        warn_threshold = config.get("warn_threshold", 3)
        warn_action = config.get("warn_action", "mute")
        warn_duration = config.get("warn_duration", 3600)

        if warn_count >= warn_threshold:
            threshold_reached = True
            auto_action = warn_action

            if warn_action == "mute":
                await self.mute_user(
                    target, warn_duration, "Auto: Too many warnings", silent=True
                )
            elif warn_action == "kick":
                await self.kick_user(target, "Auto: Too many warnings")
            elif warn_action == "ban":
                await self.ban_user(
                    target, None, "Auto: Too many warnings", silent=True
                )

        if not silent and not self._silent:
            await self.reply(
                self.i18n.t(
                    "warned",
                    target=target.mention,
                    reason=reason or "No reason provided",
                )
            )

        return WarnResult(True, warn_count, threshold_reached, auto_action)

    async def mute_user(
        self,
        target: Optional[MemberProfile] = None,
        duration: Optional[int] = None,
        reason: Optional[str] = None,
        silent: bool = False,
    ) -> bool:
        """Mute a user."""
        target = target or self.target_user
        if not target:
            raise ValueError("No target user")

        until = None
        if duration:
            until = datetime.utcnow() + timedelta(seconds=duration)

        try:
            await self.bot.restrict_chat_member(
                chat_id=self.group.telegram_id,
                user_id=target.telegram_id,
                permissions={
                    "can_send_messages": False,
                    "can_send_media_messages": False,
                    "can_send_polls": False,
                    "can_send_other_messages": False,
                    "can_add_web_page_previews": False,
                    "can_change_info": False,
                    "can_invite_users": False,
                    "can_pin_messages": False,
                },
                until_date=until,
            )

            if self.db:

                await self.db.execute(f"""
                    UPDATE members
                    SET is_muted = TRUE, mute_until = '{until.isoformat() if until else None}'
                    WHERE id = {target.id}
                    """)

                await self.log_action(
                    ActionType.MUTE,
                    target,
                    reason,
                    duration,
                    silent=silent,
                )

            if not silent and not self._silent:
                duration_str = (
                    self._format_duration(duration) if duration else "permanent"
                )
                await self.reply(
                    self.i18n.t(
                        "muted",
                        target=target.mention,
                        duration=duration_str,
                        reason=reason or "No reason provided",
                    )
                )

            return True
        except Exception as e:
            print(f"Error muting user: {e}")
            return False

    async def unmute_user(
        self,
        target: Optional[MemberProfile] = None,
        reason: Optional[str] = None,
        silent: bool = False,
    ) -> bool:
        """Unmute a user."""
        target = target or self.target_user
        if not target:
            raise ValueError("No target user")

        try:
            await self.bot.restrict_chat_member(
                chat_id=self.group.telegram_id,
                user_id=target.telegram_id,
                permissions={
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_polls": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                },
            )

            if self.db:

                await self.db.execute(f"""
                    UPDATE members
                    SET is_muted = FALSE, mute_until = NULL
                    WHERE id = {target.id}
                    """)

                await self.log_action(
                    ActionType.UNMUTE,
                    target,
                    reason,
                    silent=silent,
                )

            return True
        except Exception as e:
            print(f"Error unmuting user: {e}")
            return False

    async def ban_user(
        self,
        target: Optional[MemberProfile] = None,
        duration: Optional[int] = None,
        reason: Optional[str] = None,
        silent: bool = False,
    ) -> bool:
        """Ban a user."""
        target = target or self.target_user
        if not target:
            raise ValueError("No target user")

        until = None
        if duration:
            until = datetime.utcnow() + timedelta(seconds=duration)

        try:
            await self.bot.ban_chat_member(
                chat_id=self.group.telegram_id,
                user_id=target.telegram_id,
                until_date=until,
                revoke_messages=True,
            )

            if self.db:

                await self.db.execute(f"""
                    UPDATE members
                    SET is_banned = TRUE, ban_until = '{until.isoformat() if until else None}'
                    WHERE id = {target.id}
                    """)

                await self.log_action(
                    ActionType.BAN,
                    target,
                    reason,
                    duration,
                    silent=silent,
                )

            if not silent and not self._silent:
                await self.reply(
                    self.i18n.t(
                        "banned",
                        target=target.mention,
                        reason=reason or "No reason provided",
                    )
                )

            return True
        except Exception as e:
            print(f"Error banning user: {e}")
            return False

    async def unban_user(
        self,
        target: Optional[MemberProfile] = None,
        reason: Optional[str] = None,
        silent: bool = False,
    ) -> bool:
        """Unban a user."""
        target = target or self.target_user
        if not target:
            raise ValueError("No target user")

        try:
            await self.bot.unban_chat_member(
                chat_id=self.group.telegram_id,
                user_id=target.telegram_id,
            )

            if self.db:

                await self.db.execute(f"""
                    UPDATE members
                    SET is_banned = FALSE, ban_until = NULL
                    WHERE id = {target.id}
                    """)

                await self.log_action(
                    ActionType.UNBAN,
                    target,
                    reason,
                    silent=silent,
                )

            return True
        except Exception as e:
            print(f"Error unbanning user: {e}")
            return False

    async def kick_user(
        self,
        target: Optional[MemberProfile] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Kick a user."""
        target = target or self.target_user
        if not target:
            raise ValueError("No target user")

        try:
            await self.bot.ban_chat_member(
                chat_id=self.group.telegram_id,
                user_id=target.telegram_id,
            )
            await self.bot.unban_chat_member(
                chat_id=self.group.telegram_id,
                user_id=target.telegram_id,
            )

            if self.db:
                await self.log_action(
                    ActionType.KICK,
                    target,
                    reason,
                )

            if not self._silent:
                await self.reply(
                    self.i18n.t(
                        "kicked",
                        target=target.mention,
                        reason=reason or "No reason provided",
                    )
                )

            return True
        except Exception as e:
            print(f"Error kicking user: {e}")
            return False

    async def update_trust_score(
        self,
        user_id: int,
        delta: int,
        reason: str,
    ) -> int:
        """Update a user's trust score."""
        if not self.db:
            return 50


        result = await self.db.execute(f"""
            UPDATE members
            SET trust_score = GREATEST(0, LEAST(100, trust_score + {delta}))
            WHERE group_id = {self.group.id} AND user_id = {user_id}
            RETURNING trust_score
            """)
        return result.scalar() or 50

    async def award_xp(
        self,
        user_id: int,
        amount: int,
        reason: str,
    ) -> Tuple[int, int]:
        """Award XP to a user. Returns (new_xp, new_level)."""
        if not self.db:
            return 0, 1


        result = await self.db.execute(f"""
            UPDATE members
            SET xp = xp + {amount},
                level = CASE
                    WHEN xp + {amount} >= (level * 100) THEN level + 1
                    ELSE level
                END
            WHERE group_id = {self.group.id} AND user_id = {user_id}
            RETURNING xp, level
            """)
        row = result.fetchone()
        return row[0] if row else 0, row[1] if row else 1

    async def get_user_history(self, user_id: int) -> UserHistory:
        """Get user's moderation history."""
        if not self.db:
            return UserHistory(0, 0, 0, 0, None, None, None, 0, [])


        # Get counts
        result = await self.db.execute(f"""
            SELECT
                COUNT(CASE WHEN action_type = 'warn' THEN 1 END),
                COUNT(CASE WHEN action_type = 'mute' THEN 1 END),
                COUNT(CASE WHEN action_type = 'ban' THEN 1 END),
                COUNT(CASE WHEN action_type = 'kick' THEN 1 END),
                MAX(CASE WHEN action_type = 'warn' THEN created_at END),
                MAX(CASE WHEN action_type = 'mute' THEN created_at END),
                MAX(CASE WHEN action_type = 'ban' THEN created_at END)
            FROM mod_actions
            WHERE group_id = {self.group.id} AND target_user_id = {user_id}
            """)
        row = result.fetchone()

        # Get member stats
        member_result = await self.db.execute(f"""
            SELECT message_count FROM members
            WHERE group_id = {self.group.id} AND user_id = {user_id}
            """)
        msg_count = member_result.scalar() or 0

        return UserHistory(
            warnings=row[0] or 0,
            mutes=row[1] or 0,
            bans=row[2] or 0,
            kicks=row[3] or 0,
            last_warning=row[4],
            last_mute=row[5],
            last_ban=row[6],
            total_messages=msg_count,
            trust_score_history=[],  # Could be fetched from separate table
        )

    async def send_dm(
        self,
        user_id: int,
        text: str,
        buttons: Optional[List[List[Dict[str, str]]]] = None,
    ) -> bool:
        """Send a direct message to a user."""
        try:
            reply_markup = None
            if buttons:
                keyboard = [
                    [
                        InlineKeyboardButton(
                            text=btn["text"],
                            url=btn.get("url"),
                            callback_data=btn.get("callback_data"),
                        )
                        for btn in row
                    ]
                    for row in buttons
                ]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            # Get telegram_id from user_id
            if self.db:

                result = await self.db.execute(
                    f"SELECT telegram_id FROM users WHERE id = {user_id}"
                )
                telegram_id = result.scalar()
                if telegram_id:
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=text,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                    )
                    return True
            return False
        except Exception as e:
            print(f"Error sending DM: {e}")
            return False

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        elif seconds < 604800:
            return f"{seconds // 86400}d"
        else:
            return f"{seconds // 604800}w"

    def parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse duration string to seconds."""
        if not duration_str:
            return None

        duration_str = duration_str.lower().strip()
        multipliers = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800,
        }

        for suffix, multiplier in multipliers.items():
            if duration_str.endswith(suffix):
                try:
                    return int(duration_str[:-1]) * multiplier
                except ValueError:
                    return None

        # Try plain number (assume seconds)
        try:
            return int(duration_str)
        except ValueError:
            return None
